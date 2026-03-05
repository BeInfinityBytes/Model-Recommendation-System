# src/model_selection/api/routes/recommendation.py
"""Routes for receiving usecases and clarifications."""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from typing import Any
from src.shared.utils.logger import get_logger
from src.model_selection.api.schemas.request import UsecaseRequest, ClarificationAnswerInput
from src.model_selection.api.schemas.response import UsecaseAnalysisResponse, ClarifyResponse

logger = get_logger(__name__)
router = APIRouter()

# NOTE: service layer will be wired in Part B/C; for now we import lazily to avoid circular imports


@router.post("/usecase/analyze", response_model=UsecaseAnalysisResponse)
async def analyze_usecase(payload: UsecaseRequest):
    """
    Analyze a user usecase. This endpoint returns initial analysis and (if needed)
    generated clarification questions.
    """
    # Lazy import to avoid circular import in initial skeleton
    from src.model_selection.services.clarification_service import ClarificationService

    svc = ClarificationService()
    try:
        result = svc.analyze_usecase(payload.usecase_text)
    except Exception as e:
        logger.error("analyze_usecase_failed", error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Analysis failed")
    return result


@router.post("/usecase/{session_id}/clarify", response_model=ClarifyResponse)
async def submit_clarification(session_id: str, answers: ClarificationAnswerInput):
    """Submit clarification answers for a session and get updated context."""
    from src.model_selection.services.clarification_service import ClarificationService

    svc = ClarificationService()
    try:
        updated = svc.process_clarification_answers(session_id, answers.dict())
    except ValueError as ve:
        logger.warning("invalid_clarification_input", error=str(ve))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error("process_clarification_failed", error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Processing failed")
    return updated
