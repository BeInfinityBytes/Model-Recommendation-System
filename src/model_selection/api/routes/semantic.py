#C:\Users\Admin\Desktop\Internship\modeliq-backend\model-iq-tech-backend\src\model_selection\api\routes\semantic.py
from fastapi import APIRouter, HTTPException

from src.model_selection.services.semantic_recommendation_service import (
    get_semantic_recommendations_by_session
)
from src.shared.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("/recommend/session/{session_id}/semantic")
async def semantic_recommend(session_id: str):
    try:
        result = await get_semantic_recommendations_by_session(session_id)
        return result
    except Exception as e:
        logger.exception("Semantic recommendation failed")
        raise HTTPException(status_code=500, detail=str(e))
