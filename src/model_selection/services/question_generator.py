from __future__ import annotations
import json
import os
import logging
from typing import List, Dict, Any

from src.shared.core.llm_client import GeminiLLMClient
from src.shared.utils.logger import get_logger

from src.model_selection.models.clarification import ClarificationResponse

logger = get_logger(__name__)

# Small helper to safely find JSON inside LLM text


def _extract_json_blob(raw: str) -> str:
    raw = raw.strip()
    # Fast-path: if raw starts with { or [
    if raw.startswith("{") or raw.startswith("["):
        return raw
    # Otherwise try to find first "{" and last "}"
    i = raw.find("{")
    j = raw.rfind("}")
    if i != -1 and j != -1 and j > i:
        return raw[i:j+1]
    # fallback: return raw (will error at json.loads if invalid)
    return raw


class ClarificationQuestionGenerator:
    """
    Generates clarification questions + suggested answers + auto-filled defaults
    using the parameter constraints from range_analysis.json.
    """

    def __init__(self, llm: GeminiLLMClient):
        self.llm = llm

        PROJECT_ROOT = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../../")
        )

        JSON_PATH = os.path.join(PROJECT_ROOT, "range_analysis.json")

        if not os.path.exists(JSON_PATH):
            raise FileNotFoundError(
                f"range_analysis.json not found at: {JSON_PATH}"
            )

        with open(JSON_PATH, "r", encoding="utf-8") as f:
            self.param_constraints = json.load(f)

    async def generate(self, usecase_text: str) -> Dict[str, Any]:
        prompt = self._build_prompt(usecase_text)
        resp = await self.llm.generate_text(prompt)
        raw = resp.get("text", "") if isinstance(resp, dict) else ""
        return self._parse_raw(raw)

    def generate_sync(self, usecase_text: str) -> Dict[str, Any]:
        prompt = self._build_prompt(usecase_text)
        resp = self.llm.generate_text_sync(prompt)
        raw = resp.get("text", "") if isinstance(resp, dict) else ""
        return self._parse_raw(raw)

    def _build_prompt(self, usecase_text: str) -> str:
        constraint_json = json.dumps(self.param_constraints, indent=2)

        # NOTE: We strictly instruct LLM to use only mcq or text types.
        return f"""
You are a Clarification Question Generator for a Model Recommendation System.

User Use Case:
\"\"\"{usecase_text}\"\"\"

------------------------------------
PARAMETER CONSTRAINTS (metadata):
{constraint_json}
------------------------------------

RULES (must follow exactly):

1) SELECT only relevant parameters for this use-case (do NOT generate questions for irrelevant params).

2) ASK questions only when user input is necessary (do not ask if you can confidently infer the value).

3) NEVER output exact numeric values. Use BUCKETS or RANGES (e.g., "0–1K", "Medium (3–13B)").

4) Question type MUST be either "mcq" (multiple choice, single selection) or "text".
   - DO NOT use "checkbox" or other types.

5) Output MUST be valid JSON, exactly with these top-level fields:
   - summary: string
   - is_ambiguous: boolean
   - ambiguity_reasons: list of strings
   - generated_questions: list of objects (id, parameter, type, question, options (if mcq), suggested_answer)
   - auto_filled_defaults: object map of parameter -> inferred value

6) For auto_filled_defaults include ONLY parameters you can confidently infer and that do NOT require user input.

Return ONLY JSON (no explanatory text).

Example response:
{{
  "summary": "short summary",
  "is_ambiguous": true,
  "ambiguity_reasons": [],
  "generated_questions": [
    {{
      "id": "q1",
      "parameter": "tasks",
      "type": "mcq",
      "question": "Which task best fits?",
      "options": ["text-generation","summarization","classification"],
      "suggested_answer": "text-generation"
    }}
  ],
  "auto_filled_defaults": {{
    "language_support": "English",
    "parameter_bucket": "Medium (3–13B)"
  }}
}}
"""

    def _parse_raw(self, raw: str) -> Dict[str, Any]:
        """
        Parse LLM JSON output:
        - Extract JSON blob
        - Validate via Pydantic ClarificationResponse
        - On validation failure, return safe empty structure
        """
        try:
            blob = _extract_json_blob(raw)
            data = json.loads(blob)
        except Exception as e:
            logger.error("LLM JSON extraction/parsing failed",
                         error=str(e), raw=raw)
            return {"summary": "", "is_ambiguous": False, "ambiguity_reasons": [], "generated_questions": [], "auto_filled_defaults": {}}

        try:
            validated = ClarificationResponse(**data)
        except Exception as exc:
            # Log detailed error and raw payload for inspection
            logger.error("ClarificationResponse validation error",
                         error=str(exc), raw=data)
            # Fallback: try to salvage minimal fields if present
            summary = data.get("summary", "")
            is_ambig = bool(data.get("is_ambiguous", False))
            defaults = data.get("auto_filled_defaults", {}) if isinstance(
                data.get("auto_filled_defaults", {}), dict) else {}
            # Return safe shape
            return {
                "summary": summary,
                "is_ambiguous": is_ambig,
                "ambiguity_reasons": data.get("ambiguity_reasons", []),
                "generated_questions": [],
                "auto_filled_defaults": defaults
            }

        return validated.model_dump()
