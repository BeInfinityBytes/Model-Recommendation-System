# src/shared/utils/config.py
from typing import Dict, Any
from ..config.settings import settings

def get_app_info() -> Dict[str, Any]:
    return {
        "app_name": "model-iq-tech-backend",
        "standards_url": settings.MODEL_SELECTION_STANDARDS_URL,
    }
