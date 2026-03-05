import pytest
from fastapi.testclient import TestClient

from src.model_selection.api.main import app
from unittest.mock import patch


client = TestClient(app)


@patch("src.model_selection.services.clarification_service.ClarificationService.analyze_usecase")
def test_analyze_endpoint(mock_service):
    # Mock service response
    mock_service.return_value = {
        "session_id": "123",
        "summary": "Short summary",
        "ambiguous": True,
        "questions": [
            {"id": "q1", "type": "text", "question": "What is image size?"}
        ],
    }

    payload = {"usecase_text": "I want to detect plant disease."}

    res = client.post("/usecase/analyze", json=payload)

    assert res.status_code == 200
    body = res.json()

    assert body["session_id"] == "123"
    assert body["summary"] == "Short summary"
    assert body["ambiguous"] is True
    assert len(body["questions"]) == 1
    assert body["questions"][0]["id"] == "q1"
