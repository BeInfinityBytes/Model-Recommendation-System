# src/model_selection/api/schemas/request.py
from __future__ import annotations
from typing import List
from pydantic import BaseModel, Field


class UsecaseRequest(BaseModel):
    usecase_text: str = Field(..., example="Detect plant disease from images.")


class UsecaseAnalysisRequest(BaseModel):
    usecase_text: str = Field(...,
                              example="I want a model to classify crop images.")


class ClarificationAnswerItem(BaseModel):
    question_id: str
    answer: str | List[str]


class ClarificationAnswerInput(BaseModel):
    session_id: str
    answers: List[ClarificationAnswerItem]
