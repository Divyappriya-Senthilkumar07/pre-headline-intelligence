import re
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class LanguageService:
    """
    Multilingual Language Detection Service.
    Specialized for Pre-Headline Intelligence core languages:
    - English (en)
    - Tamil (ta) (Unicode range: \u0B80-\u0BFF)
    - Hindi (hi) (Devanagari Unicode range: \u0900-\u097F)
    Uses high-precision Unicode script density analysis with langdetect fallback.
    """

    TAMIL_RANGE = re.compile(r"[\u0B80-\u0BFF]")
    HINDI_RANGE = re.compile(r"[\u0900-\u097F]")
    LATIN_RANGE = re.compile(r"[a-zA-Z]")

    @classmethod
    def detect_language(cls, text: str) -> Tuple[str, float]:
        """
        Detects primary language and returns (lang_code, confidence).
        Supported primary codes: 'ta', 'hi', 'en', or other ISO 639-1 codes.
        """
        if not text or not text.strip():
            return "unknown", 0.0

        sample = text[:2000]
        total_chars = len(sample)
        if total_chars == 0:
            return "unknown", 0.0

        tamil_count = len(cls.TAMIL_RANGE.findall(sample))
        hindi_count = len(cls.HINDI_RANGE.findall(sample))
        latin_count = len(cls.LATIN_RANGE.findall(sample))

        # Check script ratios
        if tamil_count > 5 or (tamil_count / max(1, total_chars)) > 0.15:
            conf = min(0.99, max(0.70, (tamil_count * 2) / total_chars))
            return "ta", round(conf, 2)

        if hindi_count > 5 or (hindi_count / max(1, total_chars)) > 0.15:
            conf = min(0.99, max(0.70, (hindi_count * 2) / total_chars))
            return "hi", round(conf, 2)

        if latin_count > 10:
            # Check with langdetect for European / Latin-script languages
            try:
                from langdetect import detect, detect_langs
                langs = detect_langs(sample)
                if langs:
                    top_lang = langs[0]
                    return top_lang.lang, round(top_lang.prob, 2)
            except Exception as e:
                logger.debug(f"langdetect fallback failed: {e}")
            return "en", 0.85

        return "en", 0.50
