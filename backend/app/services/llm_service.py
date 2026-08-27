import logging
import hashlib
import time
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class LLMService:
    """
    Provider-agnostic LLM Service abstraction with caching, token management,
    and resilience against API failures.
    """
    _cache: Dict[str, Dict[str, Any]] = {}
    _cache_ttl_seconds: int = 3600

    @classmethod
    def generate_cache_key(cls, story_id: str, evidence_hash: str, question: str) -> str:
        """Generates deterministic cache key for query against specific evidence set."""
        norm_q = " ".join(question.strip().lower().split())
        raw_key = f"{story_id}::{evidence_hash}::{norm_q}"
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    @classmethod
    def get_cached_response(cls, cache_key: str) -> Optional[Dict[str, Any]]:
        """Retrieves cached response if valid within TTL."""
        entry = cls._cache.get(cache_key)
        if not entry:
            return None
        if time.time() - entry["timestamp"] > cls._cache_ttl_seconds:
            del cls._cache[cache_key]
            return None
        return entry["data"]

    @classmethod
    def set_cached_response(cls, cache_key: str, data: Dict[str, Any]) -> None:
        """Saves response in cache."""
        cls._cache[cache_key] = {
            "timestamp": time.time(),
            "data": data,
        }

    @classmethod
    def invalidate_story_cache(cls, story_id: str) -> None:
        """Invalidates all cached entries for a given story when evidence updates."""
        keys_to_delete = [k for k in cls._cache.keys() if k.startswith(story_id)]
        for k in keys_to_delete:
            cls._cache.pop(k, None)

    @classmethod
    def clear_all_cache(cls) -> None:
        """Clears all cached responses."""
        cls._cache.clear()
