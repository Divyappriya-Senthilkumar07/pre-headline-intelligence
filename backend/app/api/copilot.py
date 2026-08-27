from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.services.copilot_service import GroundedCopilotService, CopilotResponse

router = APIRouter(prefix="/copilot", tags=["Grounded Analyst Copilot"])


class CopilotQueryRequest(BaseModel):
    story_id: str = Field(..., description="ID of the Story to query against")
    question: str = Field(..., min_length=3, description="Analyst question regarding this story")
    conversation_context: Optional[List[Dict[str, str]]] = Field(default=None)


@router.post("/query", response_model=CopilotResponse, summary="Query Grounded Story Copilot")
async def query_copilot(
    body: CopilotQueryRequest,
    db: AsyncSession = Depends(get_db),
) -> CopilotResponse:
    """
    Executes a zero-hallucination, strictly grounded analyst query scoped ONLY to the provided Story ID.
    Visibly cites evidence and strictly refuses ungrounded inquiries.
    """
    if not body.story_id or not body.question.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="story_id and non-empty question are required.",
        )

    response = await GroundedCopilotService.query_copilot(
        db=db,
        story_id=body.story_id,
        question=body.question,
        conversation_context=body.conversation_context,
    )
    return response
