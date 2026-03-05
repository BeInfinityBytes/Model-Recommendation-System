#recommendation_service.py
from __future__ import annotations
from typing import Any, Dict, List

from src.model_selection.services.feature_extractor import FeatureExtractor
from src.shared.core.mongodb_client import MongoDBClient
from src.shared.core.model_data_client import ModelDataMongoClient
from src.shared.utils.logger import get_logger
from src.shared.utils.mongo_encoder import bson_to_json

logger = get_logger(__name__)


class RecommendationService:
    """
    Service to recommend models using:
    1) Top-K scoring (existing, unchanged)
    2) Soft parameter-based matching (clean response version)
    """

    def __init__(self):
        # USECASE SESSIONS DB
        self.session_db = MongoDBClient()

        # MODEL DATA DB (scraped HF models)
        self.model_db = ModelDataMongoClient()

        self.extractor = FeatureExtractor()

    # ===================================================
    # 1️⃣ TOP-K RECOMMENDER (UNCHANGED – WORKING)
    # ===================================================
    async def recommend_top_k(self, session_id: str, top_k: int = 5) -> Dict[str, Any]:
        logger.info("recommend_top_k called", session_id=session_id)

        session = await self.session_db.find_one(
            {"session_id": session_id}
        )
        if not session:
            raise ValueError(f"Session {session_id} not found")

        session = bson_to_json(session)

        features = self.extractor.extract_final_features(session)

        models = await self.model_db.get_all_models_async()
        models = bson_to_json(models)

        scored = []

        for m in models:
            score = self.extractor.score_model_against_features(m, features)

            scored.append({
                "model_name": m.get("model_name"),
                "score": float(score),
                "model": {
                    "model_id": m.get("_id"),
                    "model_name": m.get("model_name"),
                    "model_url": m.get("model_url"),
                    "summary": m.get("summary"),
                    "transformer_code": m.get("transformer_code")
                }
            })

        scored.sort(key=lambda x: x["score"], reverse=True)

        return {
            "session_id": session_id,
            "top_k": top_k,
            "results": scored[:top_k]
        }

    # ===================================================
    # 2️⃣ SOFT PARAMETER-BASED MATCHING (UPDATED FUNCTION)
    # ===================================================
    async def recommend_by_parameters(self, session_id: str) -> Dict[str, Any]:
        logger.info("recommend_by_parameters called", session_id=session_id)

        session = await self.session_db.find_one(
            {"session_id": session_id}
        )
        if not session:
            raise ValueError(f"Session {session_id} not found")

        session = bson_to_json(session)
        final_params: Dict[str, Any] = session.get("final_parameters", {})

        models = await self.model_db.get_all_models_async()
        models = bson_to_json(models)

        temp_results = []

        for m in models:
            matched = 0
            total = 0

            for param, user_value in final_params.items():
                total += 1
                model_value = m.get(param)

                if model_value is None:
                    continue

                if self._soft_match(model_value, user_value):
                    matched += 1

            # Require minimum relevance
            if total > 0 and (matched / total) >= 0.4:
                temp_results.append({
                    "match_ratio": matched / total,   # INTERNAL ONLY
                    "model": {
                        "model_id": m.get("_id"),
                        "model_name": m.get("model_name"),
                        "model_url": m.get("model_url"),
                        "summary": m.get("summary"),
                        "transformer_code": m.get("transformer_code"),
                    }
                })

        # Sort internally by relevance
        temp_results.sort(key=lambda x: x["match_ratio"], reverse=True)

        # FINAL CLEAN RESPONSE (no debug fields)
        final_results = [item["model"] for item in temp_results]

        return {
            "session_id": session_id,
            "usecase_text": session.get("usecase_text"),
            "matched_model_count": len(final_results),
            "results": final_results
        }

    # ===================================================
    # 🔧 SOFT MATCHING HELPER (UNCHANGED)
    # ===================================================
    def _soft_match(self, model_value: Any, user_value: Any) -> bool:
        """
        Flexible matching rules:
        - string ⊂ string (case-insensitive)
        - list contains string
        - list ∩ list
        """

        if model_value is None or user_value is None:
            return False

        def norm(x: Any) -> str:
            return str(x).lower().strip()

        # list vs list
        if isinstance(model_value, list) and isinstance(user_value, list):
            return any(
                norm(u) in map(norm, model_value) for u in user_value
            )

        # list vs string
        if isinstance(model_value, list):
            return any(
                norm(user_value) in norm(v) for v in model_value
            )

        # string vs list
        if isinstance(user_value, list):
            return any(
                norm(v) in norm(model_value) for v in user_value
            )

        # string vs string
        return norm(user_value) in norm(model_value)
