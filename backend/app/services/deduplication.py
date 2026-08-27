import hashlib
import re
import urllib.parse
from typing import Optional


class DeduplicationService:
    """
    Deterministic Deduplication Service.
    Standardizes URLs and hashes content/media to prevent duplicate ingestion.
    (Semantic clustering and LLM dedup are strictly reserved for Phase 2).
    """

    TRACKING_PARAMS = {
        "utm_source",
        "utm_medium",
        "utm_campaign",
        "utm_term",
        "utm_content",
        "fbclid",
        "gclid",
        "ref",
        "source",
        "ocid",
        "_ga",
    }

    @classmethod
    def normalize_url(cls, url: str) -> str:
        """
        Normalizes a URL to its canonical form:
        - Lowercases scheme and host
        - Removes tracking query parameters
        - Strips fragments and trailing slashes
        """
        if not url:
            return ""

        url = url.strip()
        try:
            parsed = urllib.parse.urlparse(url)
            scheme = parsed.scheme.lower()
            netloc = parsed.netloc.lower()
            
            # Remove www. prefix for consistent comparison where appropriate
            if netloc.startswith("www."):
                netloc = netloc[4:]

            path = parsed.path.rstrip("/")
            if not path:
                path = "/"

            # Filter query parameters
            query_tuples = urllib.parse.parse_qsl(parsed.query, keep_blank_values=False)
            filtered_query = [
                (k, v) for (k, v) in query_tuples
                if k.lower() not in cls.TRACKING_PARAMS and not k.lower().startswith("utm_")
            ]
            
            # Sort params for deterministic URL ordering
            filtered_query.sort(key=lambda x: x[0])
            new_query = urllib.parse.urlencode(filtered_query)

            normalized = urllib.parse.urlunparse((scheme, netloc, path, "", new_query, ""))
            return normalized
        except Exception:
            return url.lower().rstrip("/")

    @classmethod
    def compute_content_hash(cls, text: str) -> str:
        """
        Computes SHA256 hash over normalized text content.
        """
        if not text:
            return ""
        # Normalize whitespace
        cleaned = re.sub(r"\s+", " ", text.strip().lower())
        return hashlib.sha256(cleaned.encode("utf-8")).hexdigest()

    @classmethod
    def compute_file_hash(cls, file_bytes: bytes) -> str:
        """
        Computes SHA256 hash over raw file binary data.
        """
        return hashlib.sha256(file_bytes).hexdigest()
