import logging
from app.agents.base import BaseAgent
from app.schemas.agent import (
    EvidenceInvestigationInput,
    EvidenceInvestigationOutput,
    EvidenceChainItemSchema,
)

logger = logging.getLogger(__name__)


class EvidenceInvestigationAgent(BaseAgent[EvidenceInvestigationInput, EvidenceInvestigationOutput]):
    """
    Agent 8 — Evidence & Investigation (Core Differentiator)
    Purpose: Assembles the mandatory Evidence Chain (Source → Claim → Evidence → Corroboration → Confidence)
    and powers the grounded Copilot Q&A that strictly refuses ungrounded inquiries.
    Phase 0: Foundation & typed interface.
    """
    agent_id = 8
    agent_name = "Evidence & Investigation Agent"
    description = "Assembles click-through evidence chains and executes grounded investigative copilot queries."

    async def process(self, input_data: EvidenceInvestigationInput) -> EvidenceInvestigationOutput:
        logger.info(f"[{self.agent_name}] Assembling evidence chain for story: {input_data.story_id}")

        evidence_chain = [
            EvidenceChainItemSchema(
                step_order=1,
                source_name="Tamil Nadu Regional Daily (Dinamalar)",
                claim_text="State environmental enforcement officers inspected manufacturing facility X on Tuesday morning.",
                supporting_evidence="Direct quoting of field officer inspection log reference #TN-ENV-2026-88.",
                corroboration_notes="Original on-the-ground regional reporting.",
                confidence=0.92,
            ),
            EvidenceChainItemSchema(
                step_order=2,
                source_name="Official State Pollution Control Board Gazette",
                claim_text="Notice of inquiry issued regarding emission compliance tolerances.",
                supporting_evidence="Official regulatory public register document #PCB/ENF/441.",
                corroboration_notes="Primary government document confirming inspection premise.",
                confidence=0.98,
            ),
            EvidenceChainItemSchema(
                step_order=3,
                source_name="Hindi Business Daily (Dainik Bhaskar)",
                claim_text="Company X leadership summoned for formal compliance review.",
                supporting_evidence="Corporate affairs ministry filing excerpt.",
                corroboration_notes="Independent multi-lingual cross-corroboration.",
                confidence=0.89,
            ),
        ]

        copilot_answer = None
        grounded_citations = []
        refused = False

        if input_data.query_text:
            if "confidence" in input_data.query_text.lower() or "why" in input_data.query_text.lower():
                copilot_answer = (
                    "Formation confidence is high (88%) based on 3 independent sources across 2 languages "
                    "(Tamil & Hindi) corroborated by official state gazette document #PCB/ENF/441. "
                    "No load-bearing contradictions were detected."
                )
                grounded_citations = [
                    "Dinamalar (Tamil Regional)",
                    "TN Pollution Control Board Gazette #PCB/ENF/441",
                    "Dainik Bhaskar (Hindi Business)",
                ]
            else:
                copilot_answer = "This query cannot be answered solely from the verified evidence chain in the Media Event Graph. Refusing speculation."
                refused = True

        return EvidenceInvestigationOutput(
            story_id=input_data.story_id,
            evidence_chain=evidence_chain,
            copilot_answer=copilot_answer,
            grounded_citations=grounded_citations,
            refused_ungrounded=refused,
        )
