from fastapi import APIRouter, Depends, HTTPException
from src.model_selection.api.schemas.request import (
    UsecaseAnalysisRequest,
    ClarificationAnswerInput
)
from src.model_selection.api.schemas.response import (
    UsecaseAnalysisResponse,
    GenericResponse
)
from src.shared.core.llm_client import GeminiLLMClient
from src.shared.core.mongodb_client import MongoDBClient   # <-- use session DB client
from src.model_selection.services.clarification_service import ClarificationService
from src.shared.utils.mongo_encoder import bson_to_json

router = APIRouter(prefix="/usecase", tags=["usecase"])


# Dependency provider that wires LLM + session DB (MongoDBClient)
def get_service():
    llm = GeminiLLMClient()
    db = MongoDBClient()
    return ClarificationService(llm=llm, db=db)


@router.post("/analyze", response_model=UsecaseAnalysisResponse)
async def analyze_usecase(
    payload: UsecaseAnalysisRequest,
    service: ClarificationService = Depends(get_service)
):
    try:
        result = await service.analyze_usecase(payload.usecase_text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/answer", response_model=GenericResponse)
async def submit_answers(payload: ClarificationAnswerInput):

    db = MongoDBClient()  # already bound to usecase_sessions

    # ✅ CORRECT
    session = await db.find_one({"session_id": payload.session_id})

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session = bson_to_json(session)

    questions = session.get("questions", [])
    auto_defaults = session.get("auto_defaults", {})

    user_answer_map = {
        item.question_id: item.answer for item in payload.answers
    }

    merged_questions = []
    final_parameters = {}

    for q in questions:
        qid = q.get("id")
        param = q.get("parameter")
        suggested = q.get("suggested_answer")
        user = user_answer_map.get(qid)

        final_value = user if user is not None else suggested

        merged_questions.append({
            **q,
            "user_answer": user,
            "final_answer": final_value
        })

        if param:
            final_parameters[param] = final_value

    for param, value in auto_defaults.items():
        final_parameters.setdefault(param, value)

    # ✅ CORRECT
    await db.update_one(
        {"session_id": payload.session_id},
        {
            "$set": {
                "questions": merged_questions,
                "final_parameters": final_parameters,
                "status": "completed",
                "user_answers": user_answer_map
            }
        }
    )

    return {
        "ok": True,
        "message": "Answers merged and stored successfully",
        "session_id": payload.session_id
    }
