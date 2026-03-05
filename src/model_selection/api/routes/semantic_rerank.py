from fastapi import APIRouter, HTTPException

from src.model_selection.services.semantic_rerank_service import (
    get_reranked_recommendations_by_session
)
from src.shared.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("/recommend/session/{session_id}/semantic/rerank")
async def semantic_rerank(session_id: str):
    try:
        result = await get_reranked_recommendations_by_session(session_id)
        return result
    except Exception as e:
        logger.exception("Semantic reranking failed")
        raise HTTPException(status_code=500, detail=str(e))
