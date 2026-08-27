import io
import pytest
from httpx import AsyncClient
from PIL import Image
from pypdf import PdfWriter


def create_mock_pdf_bytes(text: str = "State Regulatory Inspection Notice #TN-ENV-2026-88") -> bytes:
    """Generates a small valid PDF file in memory."""
    # Since pypdf is primarily a reader/writer, create valid minimal PDF bytes
    # or a stream
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


def create_mock_image_bytes() -> bytes:
    """Generates a small valid PNG image in memory."""
    img = Image.new("RGB", (100, 100), color=(73, 109, 137))
    out = io.BytesIO()
    img.save(out, format="PNG")
    return out.getvalue()


@pytest.mark.asyncio
async def test_text_file_upload_and_extraction(client: AsyncClient):
    """Test 1 & 8: Text file upload, extraction, and normalized article creation."""
    content = b"State environmental department confirms compliance audit for industrial sector."
    files = {"file": ("inspection_report.txt", io.BytesIO(content), "text/plain")}
    data = {"notes": "Urgent compliance leak"}

    response = await client.post("/api/v1/media/upload", files=files, data=data)
    assert response.status_code == 201
    res = response.json()
    assert res["filename"] == "inspection_report.txt"
    assert res["media_type"] == "TEXT"
    assert res["processing_status"] == "COMPLETED"
    assert "id" in res

    media_id = res["id"]

    # Check status endpoint (Test 6)
    status_resp = await client.get(f"/api/v1/media/{media_id}/status")
    assert status_resp.status_code == 200
    st = status_resp.json()
    assert st["status"] == "COMPLETED"
    assert st["is_completed"] is True
    assert st["progress_percent"] == 100

    # Check detail endpoint
    detail_resp = await client.get(f"/api/v1/media/{media_id}")
    assert detail_resp.status_code == 200
    dt = detail_resp.json()
    assert len(dt["extractions"]) == 1
    assert "compliance audit" in dt["extractions"][0]["extracted_text"]


@pytest.mark.asyncio
async def test_image_upload_and_status(client: AsyncClient):
    """Test 1: Real Image upload and status tracking."""
    img_bytes = create_mock_image_bytes()
    files = {"file": ("diagram.png", io.BytesIO(img_bytes), "image/png")}

    response = await client.post("/api/v1/media/upload", files=files)
    assert response.status_code == 201
    res = response.json()
    assert res["filename"] == "diagram.png"
    assert res["media_type"] == "IMAGE"
    assert res["processing_status"] == "COMPLETED"


@pytest.mark.asyncio
async def test_pdf_upload_and_status(client: AsyncClient):
    """Test 2: Real PDF upload and status tracking."""
    pdf_bytes = create_mock_pdf_bytes()
    files = {"file": ("gazette.pdf", io.BytesIO(pdf_bytes), "application/pdf")}

    response = await client.post("/api/v1/media/upload", files=files)
    assert response.status_code == 201
    res = response.json()
    assert res["filename"] == "gazette.pdf"
    assert res["media_type"] == "PDF"
    assert res["processing_status"] == "COMPLETED"


@pytest.mark.asyncio
async def test_unsupported_file_type_rejection(client: AsyncClient):
    """Test 4: Rejection of blocked extensions like .exe / .sh."""
    files = {"file": ("payload.exe", io.BytesIO(b"malicious_bytes"), "application/x-msdownload")}
    response = await client.post("/api/v1/media/upload", files=files)
    assert response.status_code == 415
    assert "Unsupported" in response.json()["detail"]


@pytest.mark.asyncio
async def test_empty_file_rejection(client: AsyncClient):
    """Test 4: Rejection of empty 0-byte file."""
    files = {"file": ("empty.txt", io.BytesIO(b""), "text/plain")}
    response = await client.post("/api/v1/media/upload", files=files)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_media_delete_lifecycle(client: AsyncClient):
    """Test media deletion endpoint."""
    files = {"file": ("temp.txt", io.BytesIO(b"Temporary notes"), "text/plain")}
    upload_res = await client.post("/api/v1/media/upload", files=files)
    media_id = upload_res.json()["id"]

    del_resp = await client.delete(f"/api/v1/media/{media_id}")
    assert del_resp.status_code == 200
    assert del_resp.json()["success"] is True

    # Subsequent fetch should be 404
    get_resp = await client.get(f"/api/v1/media/{media_id}")
    assert get_resp.status_code == 404
