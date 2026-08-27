import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from httpx import AsyncClient

from app.models.source import Source
from app.models.article import Article
from app.models.story import Story, story_articles, story_entities
from app.models.graph import Entity
from app.models.claim import Claim
from app.models.contradiction import Contradiction
from app.models.prediction import Prediction
from app.models.evidence import EvidenceChain
from app.models.alert import Alert

from app.services.clustering_service import StoryClusteringService
from app.services.independence_service import IndependenceService
from app.services.contradiction_service import ContradictionService
from app.services.formation_service import StoryFormationService
from app.services.prediction_service import PredictionService
from app.services.evidence_service import EvidenceService
from app.services.alert_service import AlertOrchestratorService


@pytest.mark.asyncio
async def test_phase4_e2e_positive_multilingual_scenario(client: AsyncClient, db_session: AsyncSession):
    """
    End-to-End Positive Scenario:
    08:00 Small Tamil source reports government inspection.
    08:20 Second Tamil source reports related audit development.
    08:45 Official Government document / gazette notification appears.
    09:10 Hindi publication reports regional compliance probe.
    09:30 English national publication reports it.
    
    Complete pipeline executes: Discovery -> Context -> Clustering -> Independence -> Formation -> Prediction -> Evidence Chain -> Alert Orchestration.
    """
    # 1. Ingest Sources
    src_ta1 = Source(id="src-e2e-ta1", name="Dinamalar Regional", domain="dinamalar.com", source_type="REGIONAL_MEDIA", primary_language="ta")
    src_ta2 = Source(id="src-e2e-ta2", name="Dinamani Desk", domain="dinamani.com", source_type="REGIONAL_MEDIA", primary_language="ta")
    src_gov = Source(id="src-e2e-gov", name="TN Gazette Registry", domain="tn.gov.in", source_type="GOVERNMENT", primary_language="ta")
    src_hi  = Source(id="src-e2e-hi",  name="Dainik Bhaskar", domain="bhaskar.com", source_type="REGIONAL_MEDIA", primary_language="hi")
    src_en  = Source(id="src-e2e-en",  name="The Hindu", domain="thehindu.com", source_type="REGIONAL_MEDIA", primary_language="en")
    db_session.add_all([src_ta1, src_ta2, src_gov, src_hi, src_en])
    await db_session.flush()

    # 2. Timeline articles
    t0 = datetime(2026, 8, 26, 8, 0, 0, tzinfo=timezone.utc)
    art_ta1 = Article(
        id="art-e2e-0800",
        source_id=src_ta1.id,
        title="கம்பெனி எக்ஸ் ஆலை வளாகத்தில் மாசுக் கட்டுப்பாட்டு வாரிய அதிகாரிகள் திடீர் ஆய்வு",
        url="https://dinamalar.com/chennai/company-x-probe",
        published_at=t0,
        language="ta",
        excerpt="தமிழக அரசு சுற்றுச்சூழல் மாசுக் கட்டுப்பாட்டு வாரிய அதிகாரிகள் சென்னை ஆலையில் ஆய்வு மேற்கொண்டனர்.",
        attribution_text="Dinamalar Regional",
    )
    art_ta2 = Article(
        id="art-e2e-0820",
        source_id=src_ta2.id,
        title="கம்பெனி எக்ஸ் கழிவு நீர் வெளியேற்றம் தொடர்பாக விசாரணை",
        url="https://dinamani.com/tamilnadu/company-x-probe",
        published_at=t0 + timedelta(minutes=20),
        language="ta",
        excerpt="ஆய்வுக் குழுவினர் நச்சு ரசாயன மாதிரிகளை சேகரித்து தீவிர பரிசோதனை நடத்தி வருகின்றனர்.",
        attribution_text="Dinamani Desk",
    )
    art_gov = Article(
        id="art-e2e-0845",
        source_id=src_gov.id,
        title="Government Notice: Compliance Audit Ordered for Chemical Units in Industrial Corridor",
        url="https://tn.gov.in/gazette/orders/2026/company-x-audit",
        published_at=t0 + timedelta(minutes=45),
        language="en",
        excerpt="Official gazette order directing comprehensive environmental audit of Company X manufacturing unit.",
        attribution_text="TN Gazette Registry",
    )
    art_hi = Article(
        id="art-e2e-0910",
        source_id=src_hi.id,
        title="कंपनी एक्स चेन्नई संयंत्र पर प्रदूषण नियंत्रण बोर्ड का औचक छापा",
        url="https://bhaskar.com/national/company-x-chennai",
        published_at=t0 + timedelta(minutes=70),
        language="hi",
        excerpt="तमिलनाडु प्रदूषण नियंत्रण बोर्ड ने कंपनी एक्स के संयंत्र में आपातकालीन पर्यावरण समीक्षा शुरू की।",
        attribution_text="Dainik Bhaskar",
    )
    art_en = Article(
        id="art-e2e-0930",
        source_id=src_en.id,
        title="State Pollution Control Board orders comprehensive compliance review of Company X facility",
        url="https://thehindu.com/business/company-x-plant-inspection",
        published_at=t0 + timedelta(minutes=90),
        language="en",
        excerpt="The Tamil Nadu Pollution Control Board initiated a formal inquiry into effluent discharge standards.",
        attribution_text="The Hindu",
    )
    articles = [art_ta1, art_ta2, art_gov, art_hi, art_en]
    db_session.add_all(articles)
    await db_session.flush()

    # 3. Entities
    comp_x = Entity(id="ent-e2e-x", name="Company X", canonical_name="Company X", entity_type="COMPANY")
    regulator = Entity(id="ent-e2e-reg", name="TNPCB", canonical_name="Tamil Nadu Pollution Control Board", entity_type="REGULATOR")
    db_session.add_all([comp_x, regulator])
    await db_session.flush()

    # 4. Create Story Cluster
    story = Story(
        id="story-e2e-positive",
        title="State Pollution Control Board Compliance Probe at Company X",
        status="EMERGING",
    )
    db_session.add(story)
    await db_session.flush()

    for a in articles:
        await db_session.execute(story_articles.insert().values(story_id=story.id, article_id=a.id))
    await db_session.execute(story_entities.insert().values(story_id=story.id, entity_id=comp_x.id))
    await db_session.execute(story_entities.insert().values(story_id=story.id, entity_id=regulator.id))
    await db_session.commit()

    # 5. Execute Phase 3 Intelligence (Independence, Contradiction Gate, Formation Score)
    indep_res = await IndependenceService.analyze_story_independence(db_session, story.id, articles, [comp_x, regulator])
    gate_res = await ContradictionService.evaluate_contradiction_gate(db_session, story.id, articles)
    formation_res = await StoryFormationService.compute_story_formation(db_session, story, articles, [comp_x, regulator], indep_res, gate_res)

    assert formation_res.overall_score >= 70.0
    assert indep_res.independent_sources_count >= 4
    assert gate_res.contradiction_status == "CLEAR"

    # 6. Execute Phase 4 Intelligence (Prediction, Evidence Chain, Alert Orchestration)
    pred_res = await PredictionService.generate_prediction(db_session, story, articles, [comp_x, regulator], gate_res)
    assert pred_res.prediction_status == "ELIGIBLE"
    assert pred_res.formation_probability >= 0.70
    assert pred_res.impact_level in ["HIGH", "CRITICAL"]
    assert pred_res.current_stage in ["REGIONAL", "NATIONAL"]

    chain_res = await EvidenceService.build_evidence_chain(db_session, story, articles)
    assert chain_res.chain_status == "COMPLETE"
    assert chain_res.has_sufficient_evidence is True
    assert len(chain_res.items) == 5

    res_p = await db_session.execute(select(Prediction).where(Prediction.story_id == story.id))
    pred_db = res_p.scalars().first()
    res_e = await db_session.execute(select(EvidenceChain).where(EvidenceChain.story_id == story.id))
    chain_db = res_e.scalars().first()

    alert_db = await AlertOrchestratorService.evaluate_and_create_alert(
        db=db_session,
        story=story,
        prediction=pred_db,
        evidence_chain=chain_db,
        articles=articles,
    )

    assert alert_db.status == "ACTIVE"
    assert alert_db.ranking_score > 0.30
    assert alert_db.independent_source_count >= 4
    assert len(alert_db.languages) >= 3

    # 7. Verify via HTTP API Endpoint (Emerging Feed)
    resp = await client.get("/api/v1/stories/emerging")
    assert resp.status_code == 200
    feed_items = resp.json()
    assert len(feed_items) >= 1
    top_alert = next((it for it in feed_items if it["story_id"] == story.id), None)
    assert top_alert is not None
    assert top_alert["contradiction_status"] == "CLEAR"
    assert top_alert["evidence_available"] is True


@pytest.mark.asyncio
async def test_phase4_e2e_contradiction_scenario(client: AsyncClient, db_session: AsyncSession):
    """
    End-to-End Contradiction Scenario:
    Source A says: "Government approved the expansion project."
    Source B says: "Government rejected the expansion project."
    
    Hard Contradiction Gate halts prediction and blocks alert creation.
    """
    src_a = Source(id="src-e2e-ca", name="Herald Times", domain="herald.in", source_type="REGIONAL_MEDIA", primary_language="en")
    src_b = Source(id="src-e2e-cb", name="Standard Daily", domain="standard.in", source_type="REGIONAL_MEDIA", primary_language="en")
    db_session.add_all([src_a, src_b])
    await db_session.flush()

    now = datetime.now(timezone.utc)
    art_a = Article(
        id="art-e2e-ca",
        source_id=src_a.id,
        title="Regulator confirmed: Company X manufacturing expansion approved",
        url="https://herald.in/expansion-approved",
        published_at=now,
        language="en",
        excerpt="Official statement from State Board: Company X plant expansion approved following environmental review.",
        attribution_text="Herald Times",
    )
    art_b = Article(
        id="art-e2e-cb",
        source_id=src_b.id,
        title="Regulator confirmed: Company X manufacturing expansion rejected",
        url="https://standard.in/expansion-rejected",
        published_at=now,
        language="en",
        excerpt="Official statement from State Board: Company X plant expansion rejected due to environmental violations.",
        attribution_text="Standard Daily",
    )
    db_session.add_all([art_a, art_b])
    await db_session.flush()

    story = Story(
        id="story-e2e-conflict",
        title="Company X Expansion Approval Dispute",
        status="EMERGING",
    )
    db_session.add(story)
    await db_session.flush()

    await db_session.execute(story_articles.insert().values(story_id=story.id, article_id=art_a.id))
    await db_session.execute(story_articles.insert().values(story_id=story.id, article_id=art_b.id))
    await db_session.commit()

    # 1. Run Contradiction Gate
    gate_res = await ContradictionService.evaluate_contradiction_gate(db_session, story.id, [art_a, art_b])
    assert gate_res.contradiction_status == "PREDICTION_BLOCKED"
    assert gate_res.prediction_eligible is False

    # 2. Run Prediction Service -> Must be BLOCKED
    pred_res = await PredictionService.generate_prediction(db_session, story, [art_a, art_b], [], gate_res)
    assert pred_res.prediction_status == "BLOCKED"
    assert pred_res.blocked_reason == "LOAD_BEARING_CONTRADICTION"
    assert pred_res.formation_probability == 0.0

    # 3. Build Evidence Chain
    chain_res = await EvidenceService.build_evidence_chain(db_session, story, [art_a, art_b])

    # 4. Evaluate Alert -> Must be BLOCKED
    res_p = await db_session.execute(select(Prediction).where(Prediction.story_id == story.id))
    pred_db = res_p.scalars().first()
    res_e = await db_session.execute(select(EvidenceChain).where(EvidenceChain.story_id == story.id))
    chain_db = res_e.scalars().first()

    alert_db = await AlertOrchestratorService.evaluate_and_create_alert(
        db=db_session,
        story=story,
        prediction=pred_db,
        evidence_chain=chain_db,
        articles=[art_a, art_b],
    )

    assert alert_db.status == "BLOCKED"
    assert alert_db.contradiction_status == "PREDICTION_BLOCKED"
    assert alert_db.has_unresolved_contradictions is True
    assert "Load-bearing contradiction detected" in alert_db.ranking_explanation

    # 5. Verify Story Detail Endpoint reflects Blocked status
    resp = await client.get(f"/api/v1/stories/{story.id}")
    assert resp.status_code == 200
    story_detail = resp.json()
    assert story_detail["contradiction_status"] == "PREDICTION_BLOCKED"
    assert story_detail["prediction_eligible"] is False
    assert story_detail["prediction"]["prediction_status"] == "BLOCKED"
    assert len(story_detail["contradictions"]) >= 1
