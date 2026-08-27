import os
import shutil
import logging
from PIL import Image
from app.services.extractors.base import BaseExtractor, ExtractionResult
from app.services.language_service import LanguageService

logger = logging.getLogger(__name__)


class ImageExtractor(BaseExtractor):
    """
    Image OCR Extractor.
    Extracts text from images (PNG, JPG, TIFF, WebP, etc.) using Tesseract OCR if available,
    and extracts core image dimensions and metadata.
    """

    async def extract(self, file_path: str, mime_type: str, original_filename: str) -> ExtractionResult:
        if not os.path.exists(file_path):
            return ExtractionResult(
                extraction_method="IMAGE_OCR",
                success=False,
                error_message=f"Image file not found: {file_path}",
                is_meaningful=False,
            )

        try:
            with Image.open(file_path) as img:
                width, height = img.size
                image_format = img.format or "UNKNOWN"
                mode = img.mode

                metadata = {
                    "dimensions": f"{width}x{height}",
                    "width": width,
                    "height": height,
                    "format": image_format,
                    "mode": mode,
                }

                # Check if tesseract is installed in system
                tesseract_cmd = shutil.which("tesseract")
                extracted_text = ""
                extraction_method = "IMAGE_ANALYSIS_ONLY"
                confidence = 0.50

                if tesseract_cmd:
                    try:
                        import pytesseract
                        # Run OCR across English, Hindi, Tamil if language packs available
                        extracted_text = pytesseract.image_to_string(img).strip()
                        extraction_method = "OCR_TESSERACT"
                        confidence = 0.90 if extracted_text else 0.20
                    except Exception as ocr_err:
                        logger.warning(f"Tesseract execution error on {original_filename}: {ocr_err}")
                        extraction_method = "OCR_TESSERACT_ERROR"
                else:
                    logger.info(f"Tesseract binary not found on PATH. Image metadata extracted for {original_filename}.")
                    extraction_method = "IMAGE_METADATA_EXTRACTOR"

                lang = "unknown"
                lang_conf = 0.0
                is_meaningful = False

                if extracted_text and len(extracted_text.strip()) > 10:
                    lang, lang_conf = LanguageService.detect_language(extracted_text)
                    is_meaningful = len(extracted_text.split()) >= 3

                return ExtractionResult(
                    extracted_text=extracted_text,
                    extraction_method=extraction_method,
                    confidence=confidence,
                    detected_language=lang,
                    language_confidence=lang_conf,
                    extracted_metadata=metadata,
                    is_meaningful=is_meaningful,
                    success=True,
                )

        except Exception as e:
            logger.error(f"Failed to process image {original_filename}: {e}", exc_info=True)
            return ExtractionResult(
                extraction_method="IMAGE_PROCESSING_FAILED",
                success=False,
                error_message=f"Image processing failure: {str(e)}",
                is_meaningful=False,
            )
