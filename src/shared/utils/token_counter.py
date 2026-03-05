# src/shared/utils/token_counter.py
from __future__ import annotations
from typing import List
import logging

logger = logging.getLogger(__name__)

try:
    import tiktoken
    _HAS_TIKTOKEN = True
except Exception:
    tiktoken = None
    _HAS_TIKTOKEN = False


def count_tokens_for_model(model_name: str, texts: List[str]) -> int:
    """Return an approximate token count for given texts and model.
    Falls back to a character-based approximation if tiktoken is missing.
    """
    if _HAS_TIKTOKEN:
        try:
            enc = tiktoken.encoding_for_model(model_name)
        except Exception:
            enc = tiktoken.get_encoding("gpt2")
        total = 0
        for t in texts:
            total += len(enc.encode(t))
        return total

    # fallback: approx 4 characters = 1 token
    approx = sum(max(1, len(t) // 4) for t in texts)
    logger.debug("tiktoken not available, using approx token count", approx=approx)
    return approx


def count_tokens(text: str, model_name: str = "gpt-3.5-turbo") -> int:
    """Simple helper used by LLM client to count tokens for a single string."""
    return count_tokens_for_model(model_name, [text])
