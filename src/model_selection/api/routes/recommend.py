#recommend.py
from fastapi import APIRouter, HTTPException
from src.model_selection.services.recommendation_service import RecommendationService
from src.shared.utils.logger import get_logger
from src.shared.utils.mongo_encoder import bson_to_json

router = APIRouter(prefix="/recommend", tags=["recommend"])
logger = get_logger(__name__)

# ==============================================================
# TOP-K ENDPOINT
# ==============================================================


@router.get("/session/{session_id}/top")
async def recommend_top_models(session_id: str, top_k: int = 5):
    logger.info("Incoming top-k request", session_id=session_id, top_k=top_k)

    svc = RecommendationService()

    try:
        result = await svc.recommend_top_k(session_id, top_k)
        return bson_to_json(result)

    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==============================================================
# NEW: FULL PARAMETER MATCH ENDPOINT
# ==============================================================


@router.get("/session/{session_id}/all")
async def recommend_all_matches(session_id: str):
    logger.info("Incoming full match request", session_id=session_id)

    svc = RecommendationService()

    try:
        result = await svc.recommend_by_parameters(session_id)
        return bson_to_json(result)

    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
