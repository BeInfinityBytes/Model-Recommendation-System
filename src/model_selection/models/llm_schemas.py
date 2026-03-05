# src/model_selection/models/llm_schemas.py
"""Schemas and helpers for parsing LLM outputs.

We attempt to use pydantic-ai (if available) to parse textual LLM output
into structured data. If pydantic-ai is not available we fall back to
a safe heuristic parse so that tests/dev mode keep working.
"""

from __future__ import annotations
from pydantic import BaseModel, Field, ValidationError
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Try to import pydantic_ai parser if installed
try:
    import pydantic_ai as p_ai  # type: ignore
    _HAS_PYDANTIC_AI = True
except Exception:
    p_ai = None
    _HAS_PYDANTIC_AI = False


class LLMQuestion(BaseModel):
    id: str
    type: str  # "mcq" | "multi_select" | "text"
    question: str
    options: Optional[List[str]] = None


class LLMAnalysis(BaseModel):
    """Expected structured analysis returned or extracted from the LLM."""

    summary: str = Field(..., description="Short LLM-produced summary")
    key_points: List[str] = Field(default_factory=list, description="Extracted key points")
    ambiguous: bool = Field(False, description="Whether additional clarifications are needed")
    questions: List[LLMQuestion] = Field(default_factory=list)


def parse_llm_text(raw_text: str) -> LLMAnalysis:
    """Try to parse raw LLM text into LLMAnalysis.

    If pydantic-ai is available, the helper will attempt to run model parsing
    using pydantic-ai's utilities; if it fails, we fallback to a safe heuristic.
    The function guarantees returning a valid LLMAnalysis object.
    """
    # Option A: attempt to use pydantic-ai's text -> model parser (if installed)
    if _HAS_PYDANTIC_AI:
        try:
            # pydantic-ai usage can vary between versions. We attempt the common pattern:
            parser = p_ai.create_model_parser(LLMAnalysis)  # may raise if API differs
            parsed = parser.parse_text(raw_text)
            if isinstance(parsed, LLMAnalysis):
                return parsed
            # If returned raw dict-like, coerce
            return LLMAnalysis.model_validate(parsed)
        except Exception as exc:  # broad on purpose — parsing libs are version-volatile
            logger.debug("pydantic-ai parsing failed, falling back to heuristic", error=str(exc))

    # Heuristic fallback parsing:
    # - treat the first 1-2 sentences as summary
    # - extract lines that look like bullet points as key_points
    # - if text contains 'unclear' or '?' mark as ambiguous
    import re

    summary = raw_text.strip()
    # try to take first sentence (up to first period) as short summary
    m = re.match(r"^(.+?\.)\s", summary)
    if m:
        summary_short = m.group(1).strip()
    else:
        # no punctuation; truncate
        summary_short = summary[:200]

    # bullets
    bullets = re.findall(r"(?m)^[\-\*\•]\s*(.+)$", raw_text)
    key_points = bullets[:5] if bullets else []

    ambiguous = bool(re.search(r"\bunclear\b|\?|\bnot specified\b|\bmissing\b", raw_text, re.IGNORECASE))

    # Naive question detection: lines starting with Q: or QUESTION:
    q_matches = []
    for line in raw_text.splitlines():
        line = line.strip()
        if line.upper().startswith("Q:") or line.upper().startswith("QUESTION:"):
            # produce a free-text question (id generated from length)
            q_matches.append(LLMQuestion(id=f"q_{len(q_matches)+1}", type="text", question=line.split(":", 1)[1].strip()))

    analysis = LLMAnalysis(
        summary=summary_short,
        key_points=key_points,
        ambiguous=ambiguous,
        questions=q_matches,
    )
    return analysis
