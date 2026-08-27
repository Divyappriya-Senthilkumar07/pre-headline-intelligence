from typing import List, Dict, Any
from datetime import datetime, timezone, timedelta

# Reference base timestamp for deterministic seed replays (2026-08-26 08:00:00 UTC)
BASE_TIME = datetime(2026, 8, 26, 8, 0, 0, tzinfo=timezone.utc)


def get_seed_scenarios_data() -> List[Dict[str, Any]]:
    """
    Returns the 6 deterministic seed evaluation scenarios.
    These are evaluation fixtures and do not represent real-world events.
    """
    return [
        # ---------------------------------------------------------------------
        # SCENARIO 1: SUCCESSFUL EARLY DETECTION
        # ---------------------------------------------------------------------
        {
            "id": "scenario-1-early-detection",
            "name": "Scenario 1: Successful Early Detection (Industrial Audit)",
            "description": "Story begins with local Tamil coverage, expands to regulatory document, then Hindi desk, generating early alert 2.5 hours before national mainstream headline.",
            "scenario_type": "EARLY_DETECTION",
            "dataset_version": "v1.0.0",
            "start_time": BASE_TIME,
            "end_time": BASE_TIME + timedelta(hours=4),
            "target_story_id": "story-eval-s1",
            "expected_outcome": "MAINSTREAM_HEADLINE",
            "target_milestone": "MAINSTREAM",
            "target_milestone_time": BASE_TIME + timedelta(hours=3, minutes=40),  # 11:40 AM
            "events": [
                {
                    "event_order": 1,
                    "original_timestamp": BASE_TIME,  # 08:00 AM
                    "source_name": "Dinamalar Regional Desk",
                    "domain": "dinamalar.com",
                    "language": "ta",
                    "title": "கம்பெனி எக்ஸ் ஆலையில் மாசு கட்டுப்பாட்டு வாரிய அதிகாரிகள் ஆய்வு",
                    "excerpt": "தமிழக மாசு கட்டுப்பாட்டு வாரிய அதிகாரிகள் திடீர் கள ஆய்வு மேற்கொண்டனர்.",
                    "is_syndicated_copy": False,
                    "is_load_bearing_contradiction": False,
                    "expected_relevance": "LOCAL_PRIMARY_REPORT",
                },
                {
                    "event_order": 2,
                    "original_timestamp": BASE_TIME + timedelta(minutes=20),  # 08:20 AM
                    "source_name": "Tamil Wire Syndication",
                    "domain": "tamilwire.org",
                    "language": "ta",
                    "title": "ஆலை ஆய்வு: அதிகாரிகள் தீவிர சோதனை",
                    "excerpt": "தமிழக மாசு கட்டுப்பாட்டு வாரிய அதிகாரிகள் திடீர் கள ஆய்வு மேற்கொண்டனர்.",
                    "is_syndicated_copy": True,
                    "syndication_origin": "dinamalar.com",
                    "is_load_bearing_contradiction": False,
                    "expected_relevance": "SYNDICATED_COPY",
                },
                {
                    "event_order": 3,
                    "original_timestamp": BASE_TIME + timedelta(minutes=45),  # 08:45 AM
                    "source_name": "State Gazette / Regulatory Register",
                    "domain": "tnpcb.gov.in",
                    "language": "en",
                    "title": "Compliance Audit Order #TN-PCB-2026/88 Issued for Industrial Hub",
                    "excerpt": "Official order mandating multi-member environmental compliance audit for Company X manufacturing facility.",
                    "is_syndicated_copy": False,
                    "is_load_bearing_contradiction": False,
                    "expected_relevance": "OFFICIAL_REGULATORY_DOCUMENT",
                },
                {
                    "event_order": 4,
                    "original_timestamp": BASE_TIME + timedelta(hours=1, minutes=10),  # 09:10 AM
                    "source_name": "Dainik Bhaskar Business",
                    "domain": "bhaskar.com",
                    "language": "hi",
                    "title": "कंपनी एक्स के प्लांट में प्रदूषण नियंत्रण बोर्ड का औचक निरीक्षण",
                    "excerpt": "पर्यावरण नियमों के उल्लंघन के आरोपों के बाद कंपनी एक्स के प्लांट में विशेष जांच दल भेजा गया।",
                    "is_syndicated_copy": False,
                    "is_load_bearing_contradiction": False,
                    "expected_relevance": "INDEPENDENT_CROSS_LINGUAL_CORROBORATION",
                },
                {
                    "event_order": 5,
                    "original_timestamp": BASE_TIME + timedelta(hours=2, minutes=30),  # 10:30 AM
                    "source_name": "National Financial Daily",
                    "domain": "financialdaily.com",
                    "language": "en",
                    "title": "Company X faces state regulatory review over facility emissions",
                    "excerpt": "Industrial conglomerate under compliance scrutiny following regional audits in southern manufacturing corridor.",
                    "is_syndicated_copy": False,
                    "is_load_bearing_contradiction": False,
                    "expected_relevance": "NATIONAL_MEDIA_PICKUP",
                },
                {
                    "event_order": 6,
                    "original_timestamp": BASE_TIME + timedelta(hours=3, minutes=40),  # 11:40 AM
                    "source_name": "Major Broadcast News",
                    "domain": "nationalnews.com",
                    "language": "en",
                    "title": "HEADLINE: Regulators launch probe into Company X manufacturing facilities",
                    "excerpt": "Breaking news bulletin on state-wide environmental investigation into Company X operations.",
                    "is_syndicated_copy": False,
                    "is_load_bearing_contradiction": False,
                    "expected_relevance": "MAINSTREAM_TARGET_MILESTONE",
                },
            ],
        },

        # ---------------------------------------------------------------------
        # SCENARIO 2: SYNDICATION TRAP
        # ---------------------------------------------------------------------
        {
            "id": "scenario-2-syndication-trap",
            "name": "Scenario 2: Syndication Trap (Wire Duplication)",
            "description": "One single original publisher article is rapidly republished by 4 wire portals. The system must recognize that independent source count is 1, not 5, suppressing false early alerts.",
            "scenario_type": "SYNDICATION_TRAP",
            "dataset_version": "v1.0.0",
            "start_time": BASE_TIME,
            "end_time": BASE_TIME + timedelta(hours=2),
            "target_story_id": "story-eval-s2",
            "expected_outcome": "REGIONAL_ONLY",
            "target_milestone": "MAINSTREAM",
            "target_milestone_time": None,  # Never reaches mainstream
            "events": [
                {
                    "event_order": 1,
                    "original_timestamp": BASE_TIME,
                    "source_name": "Local District Chronicle",
                    "domain": "districtchronicle.in",
                    "language": "en",
                    "title": "Warehouse permit renewal filed by local logistics unit",
                    "excerpt": "Routine annual renewal filed with municipal administration.",
                    "is_syndicated_copy": False,
                    "is_load_bearing_contradiction": False,
                    "expected_relevance": "LOCAL_PRIMARY_REPORT",
                },
                {
                    "event_order": 2,
                    "original_timestamp": BASE_TIME + timedelta(minutes=15),
                    "source_name": "Aggregator Wire A",
                    "domain": "wire-a.net",
                    "language": "en",
                    "title": "Warehouse permit renewal filed by local logistics unit",
                    "excerpt": "Routine annual renewal filed with municipal administration.",
                    "is_syndicated_copy": True,
                    "syndication_origin": "districtchronicle.in",
                    "is_load_bearing_contradiction": False,
                    "expected_relevance": "SYNDICATED_COPY",
                },
                {
                    "event_order": 3,
                    "original_timestamp": BASE_TIME + timedelta(minutes=30),
                    "source_name": "Aggregator Wire B",
                    "domain": "wire-b.net",
                    "language": "en",
                    "title": "Warehouse permit renewal filed by local logistics unit",
                    "excerpt": "Routine annual renewal filed with municipal administration.",
                    "is_syndicated_copy": True,
                    "syndication_origin": "districtchronicle.in",
                    "is_load_bearing_contradiction": False,
                    "expected_relevance": "SYNDICATED_COPY",
                },
                {
                    "event_order": 4,
                    "original_timestamp": BASE_TIME + timedelta(minutes=45),
                    "source_name": "Aggregator Wire C",
                    "domain": "wire-c.net",
                    "language": "en",
                    "title": "Warehouse permit renewal filed by local logistics unit",
                    "excerpt": "Routine annual renewal filed with municipal administration.",
                    "is_syndicated_copy": True,
                    "syndication_origin": "districtchronicle.in",
                    "is_load_bearing_contradiction": False,
                    "expected_relevance": "SYNDICATED_COPY",
                },
            ],
        },

        # ---------------------------------------------------------------------
        # SCENARIO 3: MULTILINGUAL CONVERGENCE
        # ---------------------------------------------------------------------
        {
            "id": "scenario-3-multilingual-convergence",
            "name": "Scenario 3: Multilingual Convergence (Independent Indic Desks)",
            "description": "Same core event reported independently in Tamil, Hindi, and English regional desks without shared wire copy, maximizing cross-lingual corroboration.",
            "scenario_type": "MULTILINGUAL_CONVERGENCE",
            "dataset_version": "v1.0.0",
            "start_time": BASE_TIME,
            "end_time": BASE_TIME + timedelta(hours=3),
            "target_story_id": "story-eval-s3",
            "expected_outcome": "NATIONAL_PICKUP",
            "target_milestone": "NATIONAL",
            "target_milestone_time": BASE_TIME + timedelta(hours=2, minutes=30),  # 10:30 AM
            "events": [
                {
                    "event_order": 1,
                    "original_timestamp": BASE_TIME,
                    "source_name": "Dinamani Tamil Desk",
                    "domain": "dinamani.com",
                    "language": "ta",
                    "title": "தொழிற்சாலை விரிவாக்கத்திற்கு உள்ளூர் கிராம மக்கள் எதிர்ப்பு",
                    "excerpt": "விவசாய நிலப் பயன்பாடு தொடர்பாக கிராம சபை கூட்டத்தில் தீர்மானம் நிறைவேற்றப்பட்டது.",
                    "is_syndicated_copy": False,
                    "is_load_bearing_contradiction": False,
                    "expected_relevance": "TAMIL_DESK_PRIMARY",
                },
                {
                    "event_order": 2,
                    "original_timestamp": BASE_TIME + timedelta(minutes=30),
                    "source_name": "Amar Ujala Regional",
                    "domain": "amarujala.com",
                    "language": "hi",
                    "title": "औद्योगिक इकाई के भूमि अधिग्रहण पर स्थानीय स्तर पर विरोध शुरू",
                    "excerpt": "प्रस्तावित संयंत्र के खिलाफ पंचायत में विरोध प्रस्ताव पारित किया गया।",
                    "is_syndicated_copy": False,
                    "is_load_bearing_contradiction": False,
                    "expected_relevance": "HINDI_DESK_PRIMARY",
                },
                {
                    "event_order": 3,
                    "original_timestamp": BASE_TIME + timedelta(hours=1),
                    "source_name": "Deccan Herald Regional",
                    "domain": "deccanherald.com",
                    "language": "en",
                    "title": "Land conversion dispute flares up around proposed industrial facility",
                    "excerpt": "Local village council passes unanimous resolution challenging zoning clearance.",
                    "is_syndicated_copy": False,
                    "is_load_bearing_contradiction": False,
                    "expected_relevance": "ENGLISH_DESK_PRIMARY",
                },
            ],
        },

        # ---------------------------------------------------------------------
        # SCENARIO 4: CONTRADICTION
        # ---------------------------------------------------------------------
        {
            "id": "scenario-4-contradiction",
            "name": "Scenario 4: Contradiction Gate Defense (Conflicting Factual Claims)",
            "description": "Two credible sources report diametrically opposing factual claims on permit status. The Hard Contradiction Gate must halt prediction and block alerting.",
            "scenario_type": "CONTRADICTION",
            "dataset_version": "v1.0.0",
            "start_time": BASE_TIME,
            "end_time": BASE_TIME + timedelta(hours=2),
            "target_story_id": "story-eval-s4",
            "expected_outcome": "CONFLICT_HALTED",
            "target_milestone": "MAINSTREAM",
            "target_milestone_time": None,
            "events": [
                {
                    "event_order": 1,
                    "original_timestamp": BASE_TIME,
                    "source_name": "Corporate PR Wire",
                    "domain": "businesswire.in",
                    "language": "en",
                    "title": "Company X receives environmental clearance permit for expansion",
                    "excerpt": "Company announces state authority has granted complete environmental operating permit.",
                    "is_syndicated_copy": False,
                    "is_load_bearing_contradiction": False,
                    "expected_relevance": "CLAIM_A_SOURCE",
                },
                {
                    "event_order": 2,
                    "original_timestamp": BASE_TIME + timedelta(minutes=30),
                    "source_name": "State Gazette Register",
                    "domain": "state-env.gov.in",
                    "language": "en",
                    "title": "Application #2026-99 Rejected for Environmental Clearance",
                    "excerpt": "State Pollution Board officially orders rejection of operating license due to non-compliance.",
                    "is_syndicated_copy": False,
                    "is_load_bearing_contradiction": True,
                    "expected_relevance": "CLAIM_B_SOURCE_LOAD_BEARING_CONFLICT",
                },
            ],
        },

        # ---------------------------------------------------------------------
        # SCENARIO 5: FALSE SIGNAL
        # ---------------------------------------------------------------------
        {
            "id": "scenario-5-false-signal",
            "name": "Scenario 5: False Signal (Non-Progressing Speculation)",
            "description": "A single unverified blog post makes speculative claims that are never corroborated or picked up by independent desks.",
            "scenario_type": "FALSE_SIGNAL",
            "dataset_version": "v1.0.0",
            "start_time": BASE_TIME,
            "end_time": BASE_TIME + timedelta(hours=5),
            "target_story_id": "story-eval-s5",
            "expected_outcome": "DISAPPEARED",
            "target_milestone": "MAINSTREAM",
            "target_milestone_time": None,
            "events": [
                {
                    "event_order": 1,
                    "original_timestamp": BASE_TIME,
                    "source_name": "Market Whispers Blog",
                    "domain": "marketwhispers.fringe",
                    "language": "en",
                    "title": "Rumor: Secret merger discussions initiated between rival groups",
                    "excerpt": "Unconfirmed chatter suggests potential corporate restructuring talks.",
                    "is_syndicated_copy": False,
                    "is_load_bearing_contradiction": False,
                    "expected_relevance": "UNVERIFIED_RUMOR",
                },
            ],
        },

        # ---------------------------------------------------------------------
        # SCENARIO 6: MISSED STORY
        # ---------------------------------------------------------------------
        {
            "id": "scenario-6-missed-story",
            "name": "Scenario 6: Missed Story (Sudden Breaking Flash)",
            "description": "Mainstream breaking event occurs with no prior multi-source regional reporting, demonstrating the system's honest classification of missed stories and root cause attribution.",
            "scenario_type": "MISSED_STORY",
            "dataset_version": "v1.0.0",
            "start_time": BASE_TIME,
            "end_time": BASE_TIME + timedelta(hours=3),
            "target_story_id": "story-eval-s6",
            "expected_outcome": "MAINSTREAM_HEADLINE",
            "target_milestone": "MAINSTREAM",
            "target_milestone_time": BASE_TIME + timedelta(hours=2),  # 10:00 AM
            "events": [
                {
                    "event_order": 1,
                    "original_timestamp": BASE_TIME,
                    "source_name": "Cryptic Forum Post",
                    "domain": "forum.net",
                    "language": "en",
                    "title": "Power grid fluctuation noticed in sector 4",
                    "excerpt": "Minor voltage dip observed.",
                    "is_syndicated_copy": False,
                    "is_load_bearing_contradiction": False,
                    "expected_relevance": "INSUFFICIENT_SIGNAL",
                },
                {
                    "event_order": 2,
                    "original_timestamp": BASE_TIME + timedelta(hours=2),  # 10:00 AM
                    "source_name": "Major National Wire",
                    "domain": "reuters.com",
                    "language": "en",
                    "title": "BREAKING: State-wide blackout shuts down metropolitan region",
                    "excerpt": "Massive catastrophic failure on main grid transmission line.",
                    "is_syndicated_copy": False,
                    "is_load_bearing_contradiction": False,
                    "expected_relevance": "SUDDEN_MAINSTREAM_BREAKING",
                },
            ],
        },
    ]
