from unittest.mock import AsyncMock
from src.model_selection.services.clarification_service import ClarificationService
from src.shared.core.mongodb_client import MongoDBClient


async def test_generate_questions_flow():
    mock_llm = AsyncMock()
    mock_llm.generate_text.return_value = {
        "text": """
        [
          {"id":"q1","type":"mcq","question":"Which crop?", "options":["Wheat","Rice"]}
        ]
        """
    }

    mock_db = AsyncMock(spec=MongoDBClient)

    service = ClarificationService(mock_llm, mock_db)
    result = await service.analyze_usecase("Detect plant disease?")

    assert result["ambiguous"] is True
    assert len(result["questions"]) == 1
    assert result["questions"][0]["options"] == ["Wheat", "Rice"]
