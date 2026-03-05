# src/shared/core/llm_client.py
from __future__ import annotations
import asyncio
from typing import Dict, Any, Optional
import google.generativeai as genai
from src.shared.config.settings import settings
from src.shared.utils.logger import get_logger

logger = get_logger(__name__)


class GeminiLLMClient:
    """
    Minimal Gemini client wrapper.
    - async generate_text(prompt) -> {"text": "..."}
    - sync generate_text_sync(prompt) -> {"text": "..."} for tests
    """

    def __init__(self, model: Optional[str] = None, api_key: Optional[str] = None):
        self.model_name = model or settings.GEMINI_MODEL
        self.api_key = api_key or settings.GEMINI_API_KEY
        if self.api_key is None:
            logger.warning(
                "No GEMINI_API_KEY set in settings; LLM calls will fail.")
        genai.configure(api_key=self.api_key)

    async def generate_text(self, prompt: str) -> Dict[str, Any]:
        """
        Async wrapper that runs the blocking SDK call in a threadpool.
        Returns a dict with "text".
        """
        def _sync_call():
            model = genai.GenerativeModel(self.model_name)
            try:
                # many SDK versions return .text or .output; handle robustly
                resp = model.generate_content(prompt)
                # try common attributes
                if hasattr(resp, "text"):
                    return {"text": resp.text}
                # some responses store output/generations
                if hasattr(resp, "output") and isinstance(resp.output, (list, tuple)) and len(resp.output) > 0:
                    # attempt to find string content
                    out = resp.output[0]
                    if isinstance(out, dict) and "content" in out:
                        return {"text": out["content"]}
                # fallback: string representation
                return {"text": str(resp)}
            except Exception as e:
                logger.error("Gemini sync call failed", error=str(e))
                return {"text": ""}

        # run blocking call off the event loop
        text_dict = await asyncio.get_running_loop().run_in_executor(None, _sync_call)
        return text_dict

    def generate_text_sync(self, prompt: str) -> Dict[str, Any]:
        """
        Synchronous version for tests / MagicMock compatibility.
        """
        model = genai.GenerativeModel(self.model_name)
        try:
            resp = model.generate_content(prompt)
            if hasattr(resp, "text"):
                return {"text": resp.text}
            if hasattr(resp, "output") and isinstance(resp.output, (list, tuple)) and len(resp.output) > 0:
                out = resp.output[0]
                if isinstance(out, dict) and "content" in out:
                    return {"text": out["content"]}
            return {"text": str(resp)}
        except Exception as e:
            logger.error("Gemini sync call failed", error=str(e))
            return {"text": ""}
