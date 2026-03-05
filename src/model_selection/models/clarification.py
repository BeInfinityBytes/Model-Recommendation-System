from __future__ import annotations
from typing import List, Optional, Dict
from pydantic import BaseModel, Field, validator


class GeneratedQuestion(BaseModel):
    """Structure of each clarification question."""
    id: str = Field(...)
    parameter: str = Field(...)
    # STRICT: only "mcq" or "text" allowed (Option A)
    type: str = Field(..., pattern="^(mcq|text)$")
    question: str = Field(...)
    options: Optional[List[str]] = Field(default_factory=list)
    suggested_answer: Optional[str] = None

    @validator("options", pre=True)
    def ensure_options(cls, v):
        if v is None:
            return []
        if not isinstance(v, list):
            return []
        return [str(o).strip() for o in v]

    @validator("suggested_answer", pre=True)
    def ensure_suggested_answer(cls, v):
        if v is None:
            return None
        return str(v).strip()


class ClarificationResponse(BaseModel):
    """Full output structure from LLM for clarification questions."""
    summary: Optional[str] = Field(default="")
    is_ambiguous: bool = Field(default=False)
    ambiguity_reasons: List[str] = Field(default_factory=list)
    generated_questions: List[GeneratedQuestion] = Field(default_factory=list)
    auto_filled_defaults: Dict[str, str] = Field(default_factory=dict)

    @validator("auto_filled_defaults", pre=True)
    def ensure_defaults(cls, v):
        if v is None:
            return {}
        if not isinstance(v, dict):
            return {}
        cleaned = {}
        for k, val in v.items():
            cleaned[k] = cls._normalize_value(val)
        return cleaned

    @staticmethod
    def _normalize_value(val):
        """Convert raw numeric values to fuzzy buckets or ranges."""
        if isinstance(val, (int, float)):
            # Basic bucket logic (customizable)
            if val < 1000:
                return "0–1K"
            if val < 10000:
                return "1K–10K"
            if val < 1000000:
                return "10K–1M"
            return "1M+"

        # Convert raw text to trimmed safe text
        return str(val).strip()
