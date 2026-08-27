import re
import uuid
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple

from app.models.graph import Entity, Event
from app.models.article import Article
from app.services.entity_normalizer import EntityNormalizer

logger = logging.getLogger(__name__)


class ExtractedEntityData:
    def __init__(self, raw_mention: str, canonical_name: str, entity_type: str, confidence: float = 0.90):
        self.raw_mention = raw_mention
        self.canonical_name = canonical_name
        self.entity_type = entity_type
        self.confidence = confidence

    def to_dict(self) -> Dict[str, Any]:
        return {
            "raw_mention": self.raw_mention,
            "canonical_name": self.canonical_name,
            "entity_type": self.entity_type,
            "confidence": self.confidence,
        }


class ExtractedEventData:
    def __init__(
        self,
        event_type: str,
        title: str,
        actor: Optional[str] = None,
        target: Optional[str] = None,
        location: Optional[str] = None,
        organizations_involved: Optional[List[str]] = None,
        confidence: float = 0.85,
    ):
        self.event_type = event_type
        self.title = title
        self.actor = actor
        self.target = target
        self.location = location
        self.organizations_involved = organizations_involved or []
        self.confidence = confidence

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "title": self.title,
            "actor": self.actor,
            "target": self.target,
            "location": self.location,
            "organizations_involved": self.organizations_involved,
            "confidence": self.confidence,
        }


class ContextService:
    """
    Context Extraction & Explainable Relevance Service (Agent 2 Engine).
    Extracts entities, structured events, and evaluates contextual relevance.
    """

    # Event trigger keywords across English, Tamil, and Hindi
    EVENT_TRIGGERS = {
        "inspection": ["inspect", "inspection", "audit", "visit", "probe", "check", "surveillance", "ஆய்வு", "निरीक्षण"],
        "investigation": ["investigat", "inquiry", "probe", "scrutiny", "விசாரணை", "जांच"],
        "regulatory_action": ["fine", "penalty", "notice", "sanction", "compliance notice", "order", "அறிவிப்பு", "நோட்டீஸ்", "नोटिस"],
        "approval": ["approv", "clearance", "permit", "sanction", "license", "ஒப்புதல்", "மஞ்சூரி", "मंजूरी"],
        "announcement": ["announc", "statement", "briefing", "disclos", "அறிக்கை", "घोषणा"],
        "accident": ["leak", "spill", "explosion", "fire", "hazard", "விபத்து", "दुर्घटना"],
    }

    # Known organization / regulator patterns
    KNOWN_ORGANIZATIONS = [
        ("Tamil Nadu Pollution Control Board", "REGULATOR", ["tnspcb", "pollution control board", "மாசுக்கட்டுப்பாட்டு வாரியம்", "प्रदूषण नियंत्रण बोर्ड"]),
        ("State Pollution Control Board", "REGULATOR", ["state pollution control board", "state pollution board", "spcb"]),
        ("Company X", "COMPANY", ["company x", "company-x", "கம்பெனி எக்ஸ்", "कंपनी एक्स"]),
        ("Google India", "COMPANY", ["google india", "google"]),
        ("Apple Inc", "COMPANY", ["apple inc", "apple"]),
        ("Ministry of Environment", "GOVERNMENT", ["environment ministry", "moef", "சுற்றுச்சூழல் அமைச்சகம்", "पर्यावरण मंत्रालय"]),
    ]

    KNOWN_LOCATIONS = [
        ("Tamil Nadu", ["tamil nadu", "தமிழகம்", "தமிழக அரசு", "तमिलनाडु"]),
        ("Chennai", ["chennai", "சென்னை", "चेन्नई"]),
        ("Delhi", ["delhi", "new delhi", "டெல்லி", "दिल्ली"]),
        ("Mumbai", ["mumbai", "மும்பை", "मुंबई"]),
    ]

    @classmethod
    def _matches_pattern(cls, text_lower: str, pattern_phrase: str) -> bool:
        """Unicode-safe matching for ASCII words and Indic scripts."""
        p = pattern_phrase.lower()
        if any(ord(c) > 127 for c in p):
            return p in text_lower
        return bool(re.search(r"\b" + re.escape(p) + r"\b", text_lower))

    @classmethod
    def extract_entities(cls, text: str, language: str = "en") -> List[ExtractedEntityData]:
        """
        Extracts structured entities from text preserving original language mentions.
        """
        if not text:
            return []

        text_lower = text.lower()
        results: List[ExtractedEntityData] = []
        seen_keys = set()

        # 1. Match known organizations & regulators
        for canonical, etype, aliases in cls.KNOWN_ORGANIZATIONS:
            for alias in [canonical] + aliases:
                if cls._matches_pattern(text_lower, alias):
                    norm_name, key = EntityNormalizer.normalize_entity_name(canonical, etype)
                    if key not in seen_keys:
                        seen_keys.add(key)
                        results.append(ExtractedEntityData(raw_mention=alias, canonical_name=norm_name, entity_type=etype, confidence=0.95))
                    break

        # 2. Match known locations
        for place_name, aliases in cls.KNOWN_LOCATIONS:
            for alias in [place_name] + aliases:
                if cls._matches_pattern(text_lower, alias):
                    norm_name, key = EntityNormalizer.normalize_entity_name(place_name, "PLACE")
                    if key not in seen_keys:
                        seen_keys.add(key)
                        results.append(ExtractedEntityData(raw_mention=alias, canonical_name=norm_name, entity_type="PLACE", confidence=0.90))
                    break

        # 3. Pattern-based Organization / Person extraction (Capitalized sequences in English)
        if language == "en":
            cap_matches = re.findall(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b", text)
            for m in cap_matches:
                if len(m.split()) >= 2 and m not in ["The Hindu", "Dainik Bhaskar", "State Pollution"]:
                    norm_name, key = EntityNormalizer.normalize_entity_name(m, "ORGANIZATION")
                    if key not in seen_keys and len(m) > 4:
                        seen_keys.add(key)
                        results.append(ExtractedEntityData(raw_mention=m, canonical_name=norm_name, entity_type="ORGANIZATION", confidence=0.75))

        return results

    @classmethod
    def extract_events(cls, text: str, entities: List[ExtractedEntityData], language: str = "en") -> List[ExtractedEventData]:
        """
        Extracts structured event descriptions from text.
        """
        if not text:
            return []

        text_lower = text.lower()
        events: List[ExtractedEventData] = []
        org_names = [e.canonical_name for e in entities if e.entity_type in ["COMPANY", "ORGANIZATION", "REGULATOR", "GOVERNMENT"]]
        loc_names = [e.canonical_name for e in entities if e.entity_type == "PLACE"]

        actor = next((e.canonical_name for e in entities if e.entity_type in ["REGULATOR", "GOVERNMENT"]), None)
        target = next((e.canonical_name for e in entities if e.entity_type == "COMPANY"), None)
        location = loc_names[0] if loc_names else None

        for etype, triggers in cls.EVENT_TRIGGERS.items():
            matched = any(cls._matches_pattern(text_lower, trig) for trig in triggers)
            if matched:
                first_line = text.strip().splitlines()[0]
                event_title = f"{etype.replace('_', ' ').title()} Event: {first_line[:80]}"
                events.append(
                    ExtractedEventData(
                        event_type=etype,
                        title=event_title,
                        actor=actor or "Regulatory Authority",
                        target=target or "Tracked Entity",
                        location=location,
                        organizations_involved=org_names,
                        confidence=0.88,
                    )
                )
                break

        return events

    @classmethod
    def evaluate_relevance(
        cls,
        text: str,
        entities: List[ExtractedEntityData],
        events: List[ExtractedEventData],
        watchlist_keywords: Optional[List[str]] = None,
    ) -> Tuple[bool, float, List[str], str]:
        """
        Explainable Relevance Filter.
        Distinguishes genuine tracked subject from passing keyword mentions.
        Returns: (is_relevant, score, matched_entities, reason)
        """
        if not watchlist_keywords:
            matched = [e.canonical_name for e in entities]
            return True, 0.85, matched, "Matched broad tracked intelligence entities."

        text_lower = text.lower()
        matched = []
        reasons = []

        for kw in watchlist_keywords:
            kw_clean = kw.lower().strip()

            # Disambiguation check (e.g. Apple fruit/farming vs Apple company)
            if kw_clean == "apple" and any(w in text_lower for w in ["farming", "fruit", "orchard", "harvesting"]) and not any(w in text_lower for w in ["tech", "iphone", "inc", "cupertino"]):
                reasons.append(f"Keyword '{kw}' detected only in agricultural context (Not tech company).")
                continue

            # 1. Direct entity match
            entity_match = any(kw_clean in e.canonical_name.lower() or kw_clean in e.raw_mention.lower() for e in entities)
            if entity_match:
                matched.append(kw)
                reasons.append(f"Confirmed load-bearing entity match for '{kw}'.")

            # 2. Keyword co-occurrence check
            elif cls._matches_pattern(text_lower, kw_clean):
                matched.append(kw)
                reasons.append(f"Keyword occurrence of '{kw}' verified in context.")

        if matched:
            event_boost = 0.10 if len(events) > 0 else 0.0
            score = min(0.99, 0.75 + (len(matched) * 0.10) + event_boost)
            return True, round(score, 2), matched, "; ".join(reasons)
        else:
            return False, 0.15, [], "No active watchlist entities or keywords matched in article context."
