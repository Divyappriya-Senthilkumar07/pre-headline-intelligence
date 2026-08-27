import os
import re
import logging
from app.services.extractors.base import BaseExtractor, ExtractionResult
from app.services.language_service import LanguageService

logger = logging.getLogger(__name__)


class TextExtractor(BaseExtractor):
    """
    Plain Text File Extractor.
    Decodes multi-encoding documents (UTF-8, UTF-16 with BOM, Latin-1, CP1252) and normalizes whitespace.
    """

    async def extract(self, file_path: str, mime_type: str, original_filename: str) -> ExtractionResult:
        if not os.path.exists(file_path):
            return ExtractionResult(
                extraction_method="TEXT_DECODER",
                success=False,
                error_message=f"File not found at path: {file_path}",
                is_meaningful=False,
            )

        with open(file_path, "rb") as f:
            raw_bytes = f.read()

        decoded_text = None
        used_encoding = None

        # 1. Check for UTF BOM markers
        if raw_bytes.startswith(b"\xef\xbb\xbf"):
            decoded_text = raw_bytes.decode("utf-8-sig")
            used_encoding = "utf-8-sig"
        elif raw_bytes.startswith(b"\xff\xfe") or raw_bytes.startswith(b"\xfe\xff"):
            decoded_text = raw_bytes.decode("utf-16")
            used_encoding = "utf-16"
        else:
            # 2. Try UTF-8 standard
            try:
                decoded_text = raw_bytes.decode("utf-8")
                used_encoding = "utf-8"
            except UnicodeDecodeError:
                # 3. Try standard 8-bit European / Windows encodings
                for enc in ["latin-1", "cp1252", "iso-8859-1"]:
                    try:
                        decoded_text = raw_bytes.decode(enc)
                        used_encoding = enc
                        break
                    except (UnicodeDecodeError, LookupError):
                        continue

        if decoded_text is None:
            # Final fallback with replacement
            decoded_text = raw_bytes.decode("utf-8", errors="replace")
            used_encoding = "utf-8-replace"

        # Normalize line breaks and multiple spaces
        normalized_text = re.sub(r"\r\n", "\n", decoded_text)
        normalized_text = re.sub(r"[ \t]+", " ", normalized_text)
        normalized_text = re.sub(r"\n{3,}", "\n\n", normalized_text).strip()

        # Language Detection
        lang, lang_conf = LanguageService.detect_language(normalized_text)

        # Meaningful threshold (at least 15 chars and 3 words)
        words = normalized_text.split()
        is_meaningful = len(normalized_text) >= 15 and len(words) >= 3

        return ExtractionResult(
            extracted_text=normalized_text,
            extraction_method=f"TEXT_DECODE_{used_encoding.upper().replace('-', '_')}",
            confidence=0.98 if is_meaningful else 0.5,
            detected_language=lang,
            language_confidence=lang_conf,
            extracted_metadata={
                "encoding": used_encoding,
                "character_count": len(normalized_text),
                "word_count": len(words),
                "line_count": len(normalized_text.splitlines()),
            },
            is_meaningful=is_meaningful,
            success=True,
        )
