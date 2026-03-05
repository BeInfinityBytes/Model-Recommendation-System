# src/model_selection/services/feature_extractor.py
from __future__ import annotations
from typing import Any, Dict
from src.shared.utils.logger import get_logger

logger = get_logger(__name__)


class FeatureExtractor:
    """
    Extracts comparable structured features from session data
    and scores model compatibility.
    Keep this deterministic and explainable.
    """

    def extract_final_features(self, session: dict) -> dict:
        """
        Merge suggested answers + user answers to produce final query features.
        The session document is expected to contain:
          - questions: list of {id, parameter, suggested_answer, final_answer}
          - user_answers or answers: dict (legacy)
        """
        logger.debug("Extracting features from session",
                     session_id=session.get("session_id"))
        features: dict[str, Any] = {}

        # Support both newer and older shapes
        answers_map = {}
        if isinstance(session.get("questions"), list) and session.get("questions"):
            for q in session["questions"]:
                # prefer final_answer, then user_answer, then suggested_answer
                final = q.get("final_answer")
                if final is None:
                    final = q.get("user_answer", q.get("suggested_answer"))
                # also support parameter name if present
                param = q.get("parameter") or q.get("id")
                answers_map[param] = final
        else:
            # older payload used answers dict
            answers_map = session.get(
                "answers", {}) or session.get("user_answers", {})

        # Map commonly used fields into features (expand as needed)
        features["task_type"] = answers_map.get(
            "tasks") or answers_map.get("task_type")
        features["input_type"] = answers_map.get("input_type")
        features["output_type"] = answers_map.get("output_type")
        features["max_context_length"] = answers_map.get(
            "context_window") or answers_map.get("context_window_bucket")
        features["reasoning_level"] = answers_map.get(
            "reasoning_level_bucket") or answers_map.get("reasoning_level")
        features["privacy_requirement"] = answers_map.get(
            "privacy_requirement")
        features["parameter_bucket"] = answers_map.get("parameter_bucket")
        features["parameter_count"] = answers_map.get("parameter_count")
        features["language_support"] = answers_map.get("language_support")
        features["primary_focus"] = answers_map.get("primary_focus")
        features["license"] = answers_map.get("license")

        logger.debug("Extracted features", features=features,
                     session_id=session.get("session_id"))
        return features

    def score_model_against_features(self, model: dict, features: dict) -> float:
        """
        Lightweight scoring function: returns numeric score.
        You can replace/extend to call the scoring module.
        Rules:
          - exact or strong matches increase score; partial matches get partial points.
        """
        score = 0.0

        # 1. Task / primary focus match
        q_task = features.get("task_type") or features.get("primary_focus")
        model_tasks = model.get("tasks") or model.get(
            "primary_focus") or model.get("keywords") or []
        if q_task and model_tasks:
            try:
                model_vals = [str(x).lower() for x in (
                    model_tasks if isinstance(model_tasks, list) else [model_tasks])]
                if str(q_task).lower() in model_vals:
                    score += 3.0
                else:
                    # partial substring match
                    if any(str(q_task).lower() in v or v in str(q_task).lower() for v in model_vals):
                        score += 1.5
            except Exception:
                pass

        # 2. Reasoning level
        q_reason = features.get("reasoning_level")
        m_reason = model.get("reasoning_level_bucket") or model.get(
            "reasoning_level") or model.get("reasoning")
        if q_reason and m_reason:
            if str(q_reason).lower() == str(m_reason).lower():
                score += 2.0
            else:
                score += 0.5

        # 3. Context length (if numeric)
        try:
            q_ctx = int(features.get("max_context_length") or 0)
            m_ctx = int(model.get("context_window")
                        or model.get("context_window") or 0)
            if q_ctx and m_ctx and m_ctx >= q_ctx:
                score += 2.0
            elif q_ctx and m_ctx:
                # partial credit proportional to ratio
                score += max(0.0, min(2.0, (m_ctx / (q_ctx or 1)) * 2.0))
        except Exception:
            pass

        # 4. Parameter bucket / count (rough)
        q_bucket = (features.get("parameter_bucket") or "").lower(
        ) if features.get("parameter_bucket") else None
        m_bucket = None
        if isinstance(model.get("parameter_bucket"), str):
            m_bucket = model.get("parameter_bucket").lower()
        elif model.get("parameter_count"):
            # approximate to a bucket
            try:
                params = int(model.get("parameter_count"))
                if params > 70_000_000_000:
                    m_bucket = "xlarge (>70b)"
                elif params > 13_000_000_000:
                    m_bucket = "large (13-70b)"
                elif params > 3_000_000_000:
                    m_bucket = "medium (3-13b)"
                else:
                    m_bucket = "small (<3b)"
            except Exception:
                m_bucket = None

        if q_bucket and m_bucket:
            if q_bucket in m_bucket or m_bucket in q_bucket:
                score += 1.5

        # 5. License compatibility (if specified)
        q_license = features.get("license")
        m_license = model.get("license") or model.get(
            "modification_rights") or []
        try:
            if q_license and m_license:
                if isinstance(m_license, list):
                    m_licenses = [str(x).lower() for x in m_license]
                    if str(q_license).lower() in m_licenses:
                        score += 1.0
                else:
                    if str(q_license).lower() == str(m_license).lower():
                        score += 1.0
        except Exception:
            pass

        # clamp
        final_score = float(score)
        return final_score
