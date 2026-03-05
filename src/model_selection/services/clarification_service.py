# clarification_service.py
from __future__ import annotations
import asyncio
from uuid import uuid4
from fastapi.concurrency import run_in_threadpool

from src.model_selection.services.question_generator import ClarificationQuestionGenerator
from src.shared.core.llm_client import GeminiLLMClient
from src.shared.core.mongodb_client import MongoDBClient
from src.shared.utils.logger import get_logger

logger = get_logger(__name__)


class ClarificationService:

    def __init__(self, llm: GeminiLLMClient = None, db: MongoDBClient = None):
        self.llm = llm or GeminiLLMClient()
        self.db = db or MongoDBClient()  # already bound to usecase_sessions

    def analyze_usecase(self, usecase_text: str):
        try:
            asyncio.get_running_loop()
            return self._analyze_usecase_async(usecase_text)
        except RuntimeError:
            return asyncio.run(self._analyze_usecase_sync(usecase_text))

    async def _analyze_usecase_async(self, usecase_text: str) -> dict:
        summary_resp = await self.llm.generate_text(
            f"Summarize use case:\n{usecase_text}"
        )
        summary_text = summary_resp.get("text", "")

        # ambiguous = "?" in usecase_text or len(usecase_text.split()) < 8

        # questions, auto_defaults = [], {}
        # if ambiguous:
        generator = ClarificationQuestionGenerator(self.llm)
        qdata = await generator.generate(usecase_text)

        ambiguous = qdata.get("is_ambiguous", False)
        questions = qdata.get("generated_questions", [])
        auto_defaults = qdata.get("auto_filled_defaults", {})

        session_id = str(uuid4())

        doc = {
            "session_id": session_id,
            "usecase_text": usecase_text,
            "summary": summary_text,
            "ambiguous": ambiguous,
            "questions": questions,
            "auto_defaults": auto_defaults,
            "user_answers": {},
            "final_parameters": {},
            "status": "awaiting_answers"
        }

        # ✅ CORRECT: pass ONLY document
        await run_in_threadpool(self.db.insert_one, doc)

        return {
            "session_id": session_id,
            "summary": summary_text,
            "ambiguous": ambiguous,
            "questions": questions,
            "auto_filled_defaults": auto_defaults
        }

    async def _analyze_usecase_sync(self, usecase_text: str) -> dict:
        summary_resp = self.llm.generate_text_sync(
            f"Summarize use case:\n{usecase_text}"
        )
        summary_text = summary_resp.get("text", "")

        # ambiguous = "?" in usecase_text or len(usecase_text.split()) < 8

        # questions, auto_defaults = [], {}
        # if ambiguous:
        generator = ClarificationQuestionGenerator(self.llm)
        qdata = generator.generate_sync(usecase_text)
        ambiguous = qdata.get("is_ambiguous", False)
        questions = qdata.get("generated_questions", [])
        auto_defaults = qdata.get("auto_filled_defaults", {})

        session_id = str(uuid4())

        self.db.insert_one({
            "session_id": session_id,
            "usecase_text": usecase_text,
            "summary": summary_text,
            "ambiguous": ambiguous,
            "questions": questions,
            "auto_defaults": auto_defaults,
            "user_answers": {},
            "final_parameters": {},
            "status": "awaiting_answers"
        })

        return {
            "session_id": session_id,
            "summary": summary_text,
            "ambiguous": ambiguous,
            "questions": questions,
            "auto_filled_defaults": auto_defaults
        }
