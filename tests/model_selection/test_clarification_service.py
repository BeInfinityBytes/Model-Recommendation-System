# tests/model_selection/test_clarification_service.py

import pytest
from unittest.mock import MagicMock

from src.model_selection.services.clarification_service import ClarificationService
from src.model_selection.models.llm_schemas import LLMAnalysis, LLMQuestion


def test_analyze_usecase_basic():
    # ------------------------------
    # Mock LLM client
    # ------------------------------
    mock_llm = MagicMock()
    mock_llm.generate.return_value = (
        "Short summary.\n"
        "- point A\n"
        "- point B\n"
        "Q: What is input image resolution?"
    )

    # ------------------------------
    # Mock MongoDB
    # ------------------------------
    mock_db = MagicMock()
    mock_db.insert_one.return_value = {"inserted_id": "x"}

    service = ClarificationService(llm=mock_llm, db=mock_db)

    # ------------------------------
    # Call the service
    # ------------------------------
    result = service.analyze_usecase("I want a model to detect plant disease.")

    # ------------------------------
    # Assertions
    # ------------------------------
    assert "session_id" in result
    assert result["summary"] != ""
    assert result["ambiguous"] in (True, False)
    assert isinstance(result["questions"], list)

    # questions should be parsed
    if result["questions"]:
        first_q = result["questions"][0]
        assert "id" in first_q
        assert "question" in first_q
        assert first_q["type"] == "text"

    # DB insertion must occur
    mock_db.insert_one.assert_called_once()
