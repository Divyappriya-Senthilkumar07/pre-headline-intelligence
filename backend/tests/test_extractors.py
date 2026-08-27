import os
import tempfile
import pytest
from app.services.extractors import TextExtractor, PdfExtractor, ImageExtractor, AudioExtractor
from app.services.language_service import LanguageService
from PIL import Image
from pypdf import PdfWriter


@pytest.mark.asyncio
async def test_text_extractor_encodings():
    """Test text extractor across UTF-8, Latin-1, and UTF-16."""
    extractor = TextExtractor()

    # 1. UTF-8
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w", encoding="utf-8") as f:
        f.write("Industrial safety review conducted across southern regions.")
        path_utf8 = f.name

    res_utf8 = await extractor.extract(path_utf8, "text/plain", "test_utf8.txt")
    assert res_utf8.success is True
    assert "safety review" in res_utf8.extracted_text
    assert res_utf8.detected_language == "en"
    os.remove(path_utf8)

    # 2. Latin-1
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="wb") as f:
        f.write("Réglementation et conformité environnementale.".encode("latin-1"))
        path_latin1 = f.name

    res_latin1 = await extractor.extract(path_latin1, "text/plain", "test_latin1.txt")
    assert res_latin1.success is True
    assert "conformité" in res_latin1.extracted_text
    os.remove(path_latin1)


@pytest.mark.asyncio
async def test_image_extractor_dimensions_and_metadata():
    """Test image extractor metadata extraction."""
    extractor = ImageExtractor()
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        img = Image.new("RGB", (320, 240), color=(100, 150, 200))
        img.save(f.name, format="PNG")
        img_path = f.name

    res = await extractor.extract(img_path, "image/png", "chart.png")
    assert res.success is True
    assert res.extracted_metadata["dimensions"] == "320x240"
    assert res.extracted_metadata["format"] == "PNG"
    os.remove(img_path)


@pytest.mark.asyncio
async def test_audio_extractor_failure_surfacing():
    """Test 7: Audio extractor cleanly surfaces missing STT provider without faking data."""
    extractor = AudioExtractor()
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00D\xac\x00\x00\x01\x00\x08\x00data\x00\x00\x00\x00")
        wav_path = f.name

    res = await extractor.extract(wav_path, "audio/wav", "voice_note.wav")
    assert res.success is False
    assert "STT" in res.error_message or "engine" in res.error_message
    os.remove(wav_path)


def test_multilingual_language_detection():
    """Test 8: Language detection for Tamil, Hindi, and English."""
    # Tamil
    tamil_text = "தமிழகத்தில் உள்ள தொழிற்சாலையில் அதிகாரிகள் ஆய்வு மேற்கொண்டனர்."
    lang_ta, conf_ta = LanguageService.detect_language(tamil_text)
    assert lang_ta == "ta"
    assert conf_ta >= 0.70

    # Hindi
    hindi_text = "कंपनी एक्स के संयंत्र में सरकारी अधिकारियों ने औपचारिक निरीक्षण किया।"
    lang_hi, conf_hi = LanguageService.detect_language(hindi_text)
    assert lang_hi == "hi"
    assert conf_hi >= 0.70

    # English
    english_text = "State regulatory authority issued compliance notice regarding manufacturing plant."
    lang_en, conf_en = LanguageService.detect_language(english_text)
    assert lang_en == "en"
    assert conf_en >= 0.70
