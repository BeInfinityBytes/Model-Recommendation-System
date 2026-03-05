# src/model_selection/services/scoring.py
from __future__ import annotations
from typing import Dict, Any, List

DEFAULT_WEIGHTS = {
    "tasks": 3.0,
    "primary_focus": 2.0,
    "accuracy_requirement": 2.0,
    "privacy_requirement": 2.0,
    "context_window_bucket": 1.5,
    "parameter_bucket": 1.5,
}


def score_categorical(query_val, model_val) -> float:
    if query_val is None:
        return 0.5
    if model_val is None:
        return 0.0
    if isinstance(model_val, list):
        model_vals = [str(x).lower() for x in model_val]
        if str(query_val).lower() in model_vals:
            return 1.0
        matches = sum(1 for v in model_vals if str(
            query_val).lower() in v or v in str(query_val).lower())
        return min(1.0, matches / max(1, len(model_vals)))
    else:
        return 1.0 if str(query_val).lower() == str(model_val).lower() else 0.0


def score_numeric(query_val: float, model_val: float, minv: float, maxv: float) -> float:
    if query_val is None or model_val is None:
        return 0.5
    span = float(maxv - minv) if (maxv is not None and minv is not None and maxv >
                                  minv) else max(1.0, abs(query_val) + abs(model_val))
    d = abs(float(query_val) - float(model_val)) / span
    return max(0.0, 1.0 - min(1.0, d))


def compute_score(query: Dict[str, Any], model: Dict[str, Any], constraints: Dict[str, Any], weights: Dict[str, float] = None) -> Dict[str, Any]:
    weights = weights or DEFAULT_WEIGHTS
    total_weight = 0.0
    weighted_score = 0.0
    reasons: List[str] = []

    for param, qval in query.items():
        w = weights.get(param, 1.0)
        info = constraints.get(param, {})
        ptype = info.get("type", "Limited") if info else "Limited"
        # model may have param as scalar or array
        mval = model.get(param)
        sc = 0.0
        if ptype == "Limited":
            sc = score_categorical(qval, mval)
            if sc > 0.9:
                reasons.append(f"{param}: exact match")
            elif sc > 0.4:
                reasons.append(f"{param}: partial match")
            else:
                reasons.append(f"{param}: mismatch")
        elif ptype == "Range":
            mn = info.get("min", 0)
            mx = info.get("max", 1)
            try:
                mnum = float(mval) if mval is not None else (mn + mx) / 2.0
            except Exception:
                mnum = (mn + mx) / 2.0
            sc = score_numeric(float(qval), float(mnum), float(mn), float(mx))
            reasons.append(f"{param}: numeric_similarity={sc:.2f}")
        else:
            sc = score_categorical(qval, mval)

        weighted_score += sc * w
        total_weight += w

    final_score = weighted_score / total_weight if total_weight else 0.0
    return {"score": final_score, "reasons": reasons}
