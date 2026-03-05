# tests/model_selection/test_schemas.py
import pytest
from src.model_selection.api.schemas.request import UsecaseRequest, ClarificationAnswerInput, ClarificationAnswerItem
from src.model_selection.api.schemas.response import UsecaseAnalysisResponse, ClarificationQuestionResponse
from src.model_selection.models.llm_schemas import parse_llm_text, LLMAnalysis, LLMQuestion

def test_usecase_request_validation():
    payload = {"usecase_text": "I want a model to classify crop diseases from mobile photos."}
    req = UsecaseRequest.model_validate(payload)
    assert req.usecase_text.startswith("I want a model")

def test_response_model_shape():
    q = {"id": "deploy_target", "type": "mcq", "question": "Where run?", "options": ["Mobile", "Cloud"]}
    resp = UsecaseAnalysisResponse.model_validate({
        "session_id": "s1",
        "summary": "short summary",
        "ambiguous": True,
        "questions": [q]
    })
    assert resp.session_id == "s1"
    assert isinstance(resp.questions[0], ClarificationQuestionResponse)
    assert resp.questions[0].options == ["Mobile", "Cloud"]

def test_parse_llm_text_fallback():
    raw = "This is a short summary. \n- point A\n- point B\nQ: What is the deployment target?"
    analysis = parse_llm_text(raw)
    assert isinstance(analysis, LLMAnalysis)
    assert "short summary" in analysis.summary.lower()
    assert len(analysis.key_points) >= 1
    assert analysis.ambiguous is True or isinstance(analysis.ambiguous, bool)
    # If questions detected, ensure they conform to LLMQuestion
    if analysis.questions:
        assert isinstance(analysis.questions[0], LLMQuestion)
