from __future__ import annotations
import re
from typing import Dict, Any, List, Optional


# -------------------------------------------------
# Utility helpers
# -------------------------------------------------

def _clean_text(text: str) -> str:
    if not text:
        return ""

    text = re.sub(r"http\S+|www\S+", "", text)
    text = re.sub(r"[^\w\s.,]", "", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def _normalize_array(arr: Any) -> str:
    if not arr or not isinstance(arr, list):
        return ""

    return ", ".join(
        str(x).replace("-", " ").lower()
        for x in arr
        if isinstance(x, str)
    )


def _normalize_bucket(value: str) -> str:
    if not value or value.lower() == "unknown":
        return "general"
    return value


def _normalize_tool_usage(value: str) -> str:
    if not value:
        return "not specified"
    if value.lower() == "yes":
        return "supported"
    if value.lower() == "no":
        return "not supported"
    return value


def _extract_first(arr: Any) -> str:
    if isinstance(arr, list) and arr:
        return str(arr[0])
    if isinstance(arr, str):
        return arr
    return ""


# -------------------------------------------------
# Base model inheritance helper
# -------------------------------------------------

def _resolve_field(
    model_value: Any,
    base_value: Any,
    treat_unknown_as_missing: bool = False
) -> Any:
    """
    Returns model_value if valid.
    Otherwise falls back to base_value.
    """
    if model_value:
        if treat_unknown_as_missing:
            if isinstance(model_value, str) and model_value.lower() == "unknown":
                return base_value
        return model_value

    return base_value


# -------------------------------------------------
# arXiv enrichment helpers
# -------------------------------------------------

def _normalize_arxiv_keywords(arxiv_keywords: Any, max_keywords: int = 15) -> str:
    if not isinstance(arxiv_keywords, dict):
        return ""

    collected: List[str] = []

    for _, keywords in arxiv_keywords.items():
        if isinstance(keywords, list):
            for kw in keywords:
                if isinstance(kw, str):
                    collected.append(kw.lower().strip())

    seen = set()
    unique = []
    for kw in collected:
        if kw and kw not in seen:
            seen.add(kw)
            unique.append(kw)

    return ", ".join(unique[:max_keywords])


def _extract_arxiv_capabilities(arxiv_summaries: Any, max_chars: int = 350) -> str:
    if not isinstance(arxiv_summaries, dict):
        return ""

    texts: List[str] = []

    for _, summary in arxiv_summaries.items():
        if isinstance(summary, str):
            clean = _clean_text(summary)
            if clean:
                texts.append(clean)

    if not texts:
        return ""

    combined = " ".join(texts)
    return combined[:max_chars]


# -------------------------------------------------
# Main builder
# -------------------------------------------------

def build_embedding_text(
    model_doc: Dict[str, Any],
    base_model_doc: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Builds embedding text.
    Optionally enriches using base model if provided.
    """

    # -------------------------------
    # Field Resolution (Inheritance Safe)
    # -------------------------------

    base_architecture = _extract_first(
        _resolve_field(
            model_doc.get("base_architecture_type"),
            base_model_doc.get("base_architecture_type") if base_model_doc else None
        )
    )

    primary_focus = _normalize_array(
        _resolve_field(
            model_doc.get("primary_focus"),
            base_model_doc.get("primary_focus") if base_model_doc else None
        )
    )

    tasks = _normalize_array(
        _resolve_field(
            model_doc.get("tasks"),
            base_model_doc.get("tasks") if base_model_doc else None
        )
    )

    summary = _clean_text(
        model_doc.get("summary")
        or (base_model_doc.get("summary") if base_model_doc else "")
    )

    reasoning_level = _normalize_bucket(
        _resolve_field(
            model_doc.get("reasoning_level_bucket"),
            base_model_doc.get("reasoning_level_bucket") if base_model_doc else None,
            treat_unknown_as_missing=True
        )
    )

    math_level = _normalize_bucket(
        _resolve_field(
            model_doc.get("math_proficiency_bucket"),
            base_model_doc.get("math_proficiency_bucket") if base_model_doc else None,
            treat_unknown_as_missing=True
        )
    )

    code_level = _normalize_bucket(
        _resolve_field(
            model_doc.get("code_proficiency_bucket"),
            base_model_doc.get("code_proficiency_bucket") if base_model_doc else None,
            treat_unknown_as_missing=True
        )
    )

    knowledge_level = _normalize_bucket(
        _resolve_field(
            model_doc.get("general_knowledge_bucket"),
            base_model_doc.get("general_knowledge_bucket") if base_model_doc else None,
            treat_unknown_as_missing=True
        )
    )

    tool_usage = _normalize_tool_usage(
        _resolve_field(
            model_doc.get("tool_usage"),
            base_model_doc.get("tool_usage") if base_model_doc else None
        )
    )

    # -------------------------------
    # arXiv enrichment (model level only)
    # -------------------------------

    arxiv_keywords_text = _normalize_arxiv_keywords(
        model_doc.get("arxiv_keywords")
    )

    arxiv_capabilities_text = _extract_arxiv_capabilities(
        model_doc.get("arxiv_summaries")
    )

    # -------------------------------
    # Build embedding text
    # -------------------------------

    embedding_text = f"""
This is a {base_architecture} language model.

It is designed for {primary_focus} use cases and supports {tasks}.
The model is suitable for applications involving {summary}.

It has {reasoning_level} reasoning capability.
Its math proficiency level is {math_level}.
Its code proficiency level is {code_level}.
The model has {knowledge_level} general knowledge.

Tool usage support is {tool_usage}.
It is intended for complex problem solving and advanced AI workflows.
""".strip()

    if base_model_doc and model_doc.get("base_model_id"):
        embedding_text += (
            f"\n\nThis model is derived from base model "
            f"{model_doc.get('base_model_id')} and inherits core capabilities."
        )

    if arxiv_keywords_text:
        embedding_text += f"\n\nRelevant research topics include {arxiv_keywords_text}."

    if arxiv_capabilities_text:
        embedding_text += (
            f"\n\nResearch insights suggest strengths related to "
            f"{arxiv_capabilities_text}."
        )

    # -------------------------------
    # Metadata
    # -------------------------------

    metadata = {
        "model_name": model_doc.get("model_name"),
        "parameter_bucket": model_doc.get("parameter_bucket"),
        "context_window_bucket": model_doc.get("context_window_bucket"),
        "license": _extract_first(model_doc.get("license")),
        "quantization_level": model_doc.get("quantization_level"),
        "knowledge_cutoff": model_doc.get("knowledge_cutoff"),
    }

    return {
        "embedding_text": embedding_text,
        "metadata": metadata,
    }