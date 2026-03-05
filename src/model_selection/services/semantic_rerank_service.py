#semantic_rank_service.py
from typing import Dict

from pinecone import Pinecone

from src.shared.config.settings import settings
from src.shared.utils.logger import get_logger
from src.model_selection.services.semantic_recommendation_service import (
    get_semantic_recommendations_by_session
)

logger = get_logger(__name__)


async def get_reranked_recommendations_by_session(
    session_id: str,
    semantic_top_k: int = 50,
    final_top_k: int = 5,
) -> Dict:
    """
    Two-step reranking:
    1. Semantic vector search (existing logic)
    2. Pinecone standalone reranker (bge-reranker-v2-m3)
    """

    # -------------------------------------------------
    # 1. Get semantic recommendations
    # -------------------------------------------------
    semantic_result = await get_semantic_recommendations_by_session(
        session_id=session_id,
        top_k=semantic_top_k,
    )

    semantic_matches = semantic_result.get("semantic_matches", [])
    usecase_text = semantic_result.get("usecase_text", "")

    if not semantic_matches or not usecase_text:
        return {
            "session_id": session_id,
            "reranked_matches": [],
            "message": "No semantic matches or usecase text available",
        }

    # -------------------------------------------------
    # 2. Prepare documents for reranking
    # -------------------------------------------------
    documents = []
    semantic_map = {}

    for match in semantic_matches:
        metadata = match.get("metadata", {})
        text = metadata.get("text") or metadata.get("embedding_text")

        if not text:
            continue

        model_id = match["model_id"]

        documents.append({
            "id": model_id,
            "text": text,
        })

        semantic_map[model_id] = match

    if not documents:
        return {
            "session_id": session_id,
            "reranked_matches": [],
            "message": "No valid documents for reranking",
        }

    logger.info(f"Reranking {len(documents)} candidates for session {session_id}")

    # -------------------------------------------------
    # 3. Pinecone standalone rerank (WORKING METHOD)
    # -------------------------------------------------
    pc = Pinecone(api_key=settings.PINECONE_API_KEY)

    rerank_response = pc.inference.rerank(
        model="bge-reranker-v2-m3",
        query=usecase_text,
        documents=documents,
        top_n=final_top_k,
        rank_fields=["text"],
        return_documents=True,
    )

    # -------------------------------------------------
    # 4. Merge rerank scores with semantic metadata
    # -------------------------------------------------
    reranked_matches = []

    for item in rerank_response.data:
        model_id = item.document.get("id")
        semantic_match = semantic_map.get(model_id)

        if not semantic_match:
            continue

        reranked_matches.append({
            "model_id": model_id,
            "semantic_score": semantic_match["score"],
            "rerank_score": item.score,
            "metadata": semantic_match["metadata"],
        })

    return {
        "session_id": session_id,
        "semantic_candidates": len(semantic_matches),
        "reranked_top_k": final_top_k,
        "reranked_matches": reranked_matches,
    }
