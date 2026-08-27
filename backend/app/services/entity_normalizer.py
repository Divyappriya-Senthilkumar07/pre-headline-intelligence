import re
from typing import Tuple, Dict, Any, Optional


class EntityNormalizer:
    """
    Entity Normalization and Canonical Resolution Service.
    Standardizes entity names across variations while preserving original mentions.
    Handles companies, regulatory agencies, government departments, and geographic places.
    """

    COMPANY_SUFFIXES = re.compile(
        r"\b(pvt\.?\s*ltd\.?|private\s+limited|ltd\.?|limited|inc\.?|incorporated|corp\.?|corporation|llc|co\.?)\b",
        re.IGNORECASE,
    )

    GOV_PREFIXES = re.compile(
        r"\b(ministry\s+of|department\s+of|dept\.?\s+of|state\s+pollution\s+control\s+board|spcb|cpcb)\b",
        re.IGNORECASE,
    )

    CANONICAL_ALIASES: Dict[str, str] = {
        "google": "Google",
        "google india": "Google India",
        "google india pvt ltd": "Google India",
        "google llc": "Google",
        "alphabet": "Alphabet Inc",
        "alphabet inc": "Alphabet Inc",
        "apple": "Apple Inc",
        "apple inc": "Apple Inc",
        "company x": "Company X",
        "company x pvt ltd": "Company X",
        "company-x": "Company X",
        "tnspcb": "Tamil Nadu Pollution Control Board",
        "tamil nadu pollution control board": "Tamil Nadu Pollution Control Board",
        "state pollution control board": "State Pollution Control Board",
        "cpcb": "Central Pollution Control Board",
        "central pollution control board": "Central Pollution Control Board",
        "chennai": "Chennai",
        "tamil nadu": "Tamil Nadu",
        "delhi": "Delhi",
        "new delhi": "Delhi",
    }

    @classmethod
    def normalize_entity_name(cls, raw_name: str, entity_type: str = "ORGANIZATION") -> Tuple[str, str]:
        """
        Normalizes an entity name into (canonical_name, normalized_key).
        Example: 'Google India Pvt Ltd' -> ('Google India', 'google-india')
        """
        if not raw_name or not raw_name.strip():
            return "Unknown Entity", "unknown-entity"

        cleaned = raw_name.strip()
        cleaned_lower = cleaned.lower()

        # Check known canonical aliases
        if cleaned_lower in cls.CANONICAL_ALIASES:
            canonical = cls.CANONICAL_ALIASES[cleaned_lower]
            key = re.sub(r"[^a-z0-9]+", "-", canonical.lower()).strip("-")
            return canonical, key

        # Strip company suffixes for company / organization types
        if entity_type.upper() in ["COMPANY", "ORGANIZATION"]:
            stripped = cls.COMPANY_SUFFIXES.sub("", cleaned).strip()
            stripped = re.sub(r"\s+", " ", stripped).strip(" ,.-")
            if len(stripped) >= 2:
                canonical = stripped.title()
                key = re.sub(r"[^a-z0-9]+", "-", canonical.lower()).strip("-")
                return canonical, key

        # Standard capitalization
        canonical = cleaned.strip()
        key = re.sub(r"[^a-z0-9]+", "-", canonical.lower()).strip("-")
        return canonical, key
