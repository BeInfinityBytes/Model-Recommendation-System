# tests/shared/test_llm_client.py
import pytest
from src.shared.core.llm_client import GeminiLLMClient

def test_llm_client_mock_mode(monkeypatch):
    client = GeminiLLMClient(api_key=None, model="test-model")
    prompt = "Analyze: I need an agricultural model"

    result = client.call(prompt)
    assert result.model == "test-model"
    assert result.total_tokens > 0
    assert "provider" in result.raw_response
    assert result.raw_response["provider"] == "mock"
