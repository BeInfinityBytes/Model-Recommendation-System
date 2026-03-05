#semantic_recommendation_service.py
from typing import Dict, List

from pinecone import Pinecone

from src.shared.config.settings import settings
from src.shared.core.mongodb_client import MongoDBClient
from src.model_selection.services.recommendation_service import RecommendationService
from src.model_selection.semantic.openai_embedding_client import generate_embedding
from src.shared.utils.mongo_encoder import bson_to_json
from src.shared.utils.logger import get_logger

logger = get_logger(__name__)


async def get_semantic_recommendations_by_session(
    session_id: str,
    top_k: int = 5,
) -> Dict:
    """
    Semantic recommendation flow:
    1. Load session from MongoDB
    2. Get MongoDB-filtered candidate models
    3. Create embedding for usecase + summary
    4. Semantic search in Pinecone (filtered)
    5. Return ranked results
    """

    # -------------------------------------------------
    # 1. Load session
    # -------------------------------------------------
    session_db = MongoDBClient()
    session = await session_db.find_one({"session_id": session_id})

    if not session:
        raise ValueError(f"Session {session_id} not found")

    session = bson_to_json(session)

    usecase_text = session.get("usecase_text", "")
    summary = session.get("summary", "")

    if not usecase_text and not summary:
        raise ValueError("Session has no semantic content")

    # -------------------------------------------------
    # 2. Get MongoDB-based recommendations
    # -------------------------------------------------
    recommender = RecommendationService()
    mongo_result = await recommender.recommend_by_parameters(session_id)

    candidate_models = mongo_result.get("results", [])
    if not candidate_models:
        return {
            "session_id": session_id,
            "semantic_matches": [],
            "message": "No candidate models after MongoDB filtering",
        }

    candidate_model_names = [
        m["model_name"] for m in candidate_models if m.get("model_name")
    ]

    # -------------------------------------------------
    # 3. Create query embedding
    # -------------------------------------------------
    query_text = f"""
    Use case:
    {usecase_text}

    Summary:
    {summary}
    """

    query_embedding = generate_embedding(query_text)

    # -------------------------------------------------
    # 4. Pinecone semantic search (FILTERED)
    # -------------------------------------------------
    pc = Pinecone(api_key=settings.PINECONE_API_KEY)
    index = pc.Index(settings.PINECONE_INDEX_NAME)

    response = index.query(
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True,
        filter={
            "model_name": {"$in": candidate_model_names}
        },
    )

    # -------------------------------------------------
    # 5. Format response
    # -------------------------------------------------
    semantic_matches = []

    for match in response.get("matches", []):
        semantic_matches.append({
            "model_id": match["id"],
            "score": match["score"],
            "metadata": match.get("metadata", {}),
        })

    return {
        "session_id": session_id,
        "usecase_text": usecase_text,
        "total_candidates_searched": len(candidate_model_names),
        "semantic_matches": semantic_matches,
    }