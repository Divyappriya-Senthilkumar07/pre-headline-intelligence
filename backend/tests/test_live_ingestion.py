import asyncio
import os
import io
import sys
import pytest
from PIL import Image
from pypdf import PdfWriter
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select

from app.models.base import Base
from app.models.media import Media, MediaExtraction, MediaTypeEnum, MediaProcessingStatusEnum
from app.models.article import Article
from app.models.source import Source
from app.services.media_service import MediaService
from app.services.media_processor import MediaProcessor
from app.services.rss_service import RssIngestionService
from app.services.gdelt_service import GdeltIngestionService


@pytest.mark.asyncio
async def test_full_live_ingestion_pipeline():
    # 1. Setup in-memory sqlite engine
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    os.makedirs("./test_media_uploads", exist_ok=True)

    async with async_session() as db:
        processor = MediaProcessor()

        # TEST A: Real Image Upload & Processing
        img = Image.new("RGB", (400, 300), color=(50, 100, 150))
        img_path = "./test_media_uploads/live_test_chart.png"
        img.save(img_path, format="PNG")

        media_img = await MediaService.create_media_record(
            db=db,
            original_filename="live_test_chart.png",
            mime_type="image/png",
            file_size_bytes=os.path.getsize(img_path),
            storage_reference=img_path,
            source_metadata={"analyst": "investigator_01"},
        )
        assert media_img.id is not None

        processed_img = await processor.process_media(db, media_img.id)
        assert processed_img.processing_status == MediaProcessingStatusEnum.COMPLETED.value

        ext_img_res = await db.execute(select(MediaExtraction).where(MediaExtraction.media_id == media_img.id))
        ext_img = ext_img_res.scalars().first()
        assert ext_img is not None
        assert ext_img.metadata_json["dimensions"] == "400x300"

        # TEST B: Real PDF Upload & Processing
        writer = PdfWriter()
        writer.add_blank_page(width=300, height=300)
        pdf_path = "./test_media_uploads/live_test_gazette.pdf"
        with open(pdf_path, "wb") as f:
            writer.write(f)

        media_pdf = await MediaService.create_media_record(
            db=db,
            original_filename="live_test_gazette.pdf",
            mime_type="application/pdf",
            file_size_bytes=os.path.getsize(pdf_path),
            storage_reference=pdf_path,
        )
        processed_pdf = await processor.process_media(db, media_pdf.id)
        assert processed_pdf.processing_status == MediaProcessingStatusEnum.COMPLETED.value

        # TEST C: Real Text File Upload & Normalized Article Creation
        txt_path = "./test_media_uploads/live_test_leak.txt"
        txt_content = (
            "State Pollution Control Board Audit Notice #2026-TN-09.\n"
            "Official inspection of chemical manufacturing unit scheduled for next Monday.\n"
            "Preliminary environmental monitoring flags elevated sulfur dioxide levels."
        )
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(txt_content)

        media_txt = await MediaService.create_media_record(
            db=db,
            original_filename="live_test_leak.txt",
            mime_type="text/plain",
            file_size_bytes=os.path.getsize(txt_path),
            storage_reference=txt_path,
        )
        processed_txt = await processor.process_media(db, media_txt.id)
        assert processed_txt.processing_status == MediaProcessingStatusEnum.COMPLETED.value

        art_res = await db.execute(select(Article).where(Article.url == f"media://{media_txt.id}"))
        article = art_res.scalars().first()
        assert article is not None
        assert "Audit Notice" in article.title
        assert len(article.excerpt) <= 350

        # TEST D: Multilingual RSS Ingestion & Deduplication
        rss_mock_xml = """<?xml version="1.0" encoding="UTF-8" ?>
        <rss version="2.0">
        <channel>
         <title>Regional Intelligence Wire</title>
         <link>https://regional-wire-live.example.org</link>
         <item>
          <title>தொழிற்சாலை பாதுகாப்பு ஆய்வு அறிக்கை வெளியீடு</title>
          <link>https://regional-wire-live.example.org/news/audit-report-2026</link>
          <description>அரசு அதிகாரிகள் வெளியிட்டுள்ள சமீபத்திய தகவல்கள்.</description>
          <pubDate>Wed, 26 Aug 2026 10:00:00 GMT</pubDate>
         </item>
        </channel>
        </rss>"""

        rss_stats = await RssIngestionService.ingest_feed(
            db=db,
            feed_url="https://regional-wire-live.example.org/rss.xml",
            feed_content=rss_mock_xml,
        )
        assert rss_stats["new_articles"] == 1

        rss_stats_dupe = await RssIngestionService.ingest_feed(
            db=db,
            feed_url="https://regional-wire-live.example.org/rss.xml",
            feed_content=rss_mock_xml,
        )
        assert rss_stats_dupe["new_articles"] == 0
        assert rss_stats_dupe["duplicates_skipped"] == 1

        # TEST E: GDELT GKG Ingestion
        gdelt_stats = await GdeltIngestionService.ingest_gkg_events(db)
        assert gdelt_stats["new_articles"] >= 1

    # Cleanup temp test files
    for p in [img_path, pdf_path, txt_path]:
        if os.path.exists(p):
            os.remove(p)
    if os.path.exists("./test_media_uploads"):
        try:
            os.rmdir("./test_media_uploads")
        except Exception:
            pass
