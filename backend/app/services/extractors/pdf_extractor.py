import os
import logging
from pypdf import PdfReader
from app.services.extractors.base import BaseExtractor, ExtractionResult
from app.services.language_service import LanguageService

logger = logging.getLogger(__name__)


class PdfExtractor(BaseExtractor):
    """
    PDF Document Extractor.
    Extracts direct selectable text and metadata across all pages using pypdf.
    Falls back to OCR methods when no text layer is discovered.
    """

    async def extract(self, file_path: str, mime_type: str, original_filename: str) -> ExtractionResult:
        if not os.path.exists(file_path):
            return ExtractionResult(
                extraction_method="PDF_EXTRACTOR",
                success=False,
                error_message=f"PDF file not found: {file_path}",
                is_meaningful=False,
            )

        try:
            reader = PdfReader(file_path)
            num_pages = len(reader.pages)
            extracted_pages = []
            
            for idx, page in enumerate(reader.pages):
                page_text = page.extract_text() or ""
                if page_text.strip():
                    extracted_pages.append(page_text.strip())

            full_text = "\n\n".join(extracted_pages).strip()
            
            # Read metadata
            doc_info = reader.metadata or {}
            metadata = {
                "page_count": num_pages,
                "pages_with_text": len(extracted_pages),
                "title": doc_info.get("/Title", None),
                "author": doc_info.get("/Author", None),
                "producer": doc_info.get("/Producer", None),
            }

            if full_text and len(full_text.strip()) > 10:
                lang, lang_conf = LanguageService.detect_language(full_text)
                words = full_text.split()
                is_meaningful = len(words) >= 5

                return ExtractionResult(
                    extracted_text=full_text,
                    extraction_method="PDF_DIRECT_TEXT",
                    confidence=0.95,
                    detected_language=lang,
                    language_confidence=lang_conf,
                    extracted_metadata=metadata,
                    is_meaningful=is_meaningful,
                    success=True,
                )
            else:
                # No selectable text layer found -> OCR fallback notification
                logger.info(f"PDF {original_filename} has no direct text layer. OCR fallback needed.")
                return ExtractionResult(
                    extracted_text="",
                    extraction_method="PDF_OCR_FALLBACK",
                    confidence=0.10,
                    detected_language="unknown",
                    language_confidence=0.0,
                    extracted_metadata={
                        **metadata,
                        "notice": "Scanned/image PDF detected without embedded text layer.",
                    },
                    is_meaningful=False,
                    success=True,
                    error_message=None,
                )

        except Exception as e:
            logger.error(f"Failed to process PDF {original_filename}: {e}", exc_info=True)
            return ExtractionResult(
                extraction_method="PDF_PARSER_ERROR",
                success=False,
                error_message=f"PDF parsing failure: {str(e)}",
                is_meaningful=False,
            )
