# src/model_selection/api/schemas/response.py

from __future__ import annotations
from typing import List, Optional, Any
from pydantic import BaseModel, Field

# -------------------------------------------------------
# Response returned by /usecase/analyze
# -------------------------------------------------------


class ClarificationQuestion(BaseModel):
    id: str
    type: str
    question: str
    options: Optional[List[str]] = Field(default_factory=list)
    suggested_answer: Optional[Any] = None  # LLM-generated suggested answer


class UsecaseAnalysisResponse(BaseModel):
    session_id: str
    summary: str
    ambiguous: bool
    questions: List[ClarificationQuestion] = Field(default_factory=list)


# -------------------------------------------------------
# Generic OK response for endpoints like /usecase/answer
# -------------------------------------------------------
class GenericResponse(BaseModel):
    ok: bool = True
    message: str = "Success"
    session_id: Optional[str] = None
