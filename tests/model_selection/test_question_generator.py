from unittest.mock import AsyncMock
from src.model_selection.services.question_generator import ClarificationQuestionGenerator


async def test_question_generator_parses_llm_json():
    mock_llm = AsyncMock()
    mock_llm.generate_text.return_value = {
        "text": """
        [
          {"id":"q1","type":"text","question":"What is image size?"}
        ]
        """
    }

    generator = ClarificationQuestionGenerator(mock_llm)
    result = await generator.generate("detect disease")

    assert len(result) == 1
    assert result[0]["id"] == "q1"
    assert result[0]["question"] == "What is image size?"
    assert result[0]["type"] == "text"
    assert result[0]["options"] == []
