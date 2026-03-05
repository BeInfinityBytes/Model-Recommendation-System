# C:\Users\Admin\Desktop\Internship\modeliq-backend\model-iq-tech-backend
# \src\shared\core\model_data_client.py

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pymongo import MongoClient
from fastapi.concurrency import run_in_threadpool

from src.shared.config.settings import settings
from src.shared.utils.logger import get_logger

logger = get_logger(__name__)


class ModelDataMongoClient:
    """
    Client for the remote scraped model-data DB (Atlas).
    Handles SRV and multi-host URIs correctly.
    """

    def __init__(self) -> None:
        uri = settings.MODEL_DATA_MONGO_URI
        db_name = settings.MODEL_DATA_DB
        coll = settings.MODEL_DATA_COLLECTION

        if not uri or not db_name or not coll:
            raise RuntimeError(
                "Missing MODEL_DATA_MONGO_URI / MODEL_DATA_DB / MODEL_DATA_COLLECTION"
            )

        logger.info(
            "Connecting to ModelData MongoDB",
            uri=uri,
            db=db_name,
            collection=coll,
        )

        try:
            # Atlas (mongodb+srv or multiple hosts) → NO directConnection
            if uri.startswith("mongodb+srv://") or "," in uri:
                self.client = MongoClient(uri)
            else:
                # Local MongoDB or single-host → enable directConnection
                self.client = MongoClient(uri, directConnection=True)

            self.db = self.client[db_name]
            self.collection = self.db[coll]

        except Exception as e:
            logger.error("MongoDB connection error", error=str(e))
            raise

        logger.info("Connected to model-data DB successfully")

    # ---------------------------------------------------------------------
    # Sync Methods
    # ---------------------------------------------------------------------

    def get_all_models(self) -> List[Dict[str, Any]]:
        """Fetch all model documents."""
        return list(self.collection.find({}))

    def find_models(self, filter: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find models based on a MongoDB filter."""
        return list(self.collection.find(filter))

    def get_model_by_name(self, model_name: str) -> Optional[Dict[str, Any]]:
        """
        Fetch a single model document by model_name.

        Args:
            model_name: Name of the model.

        Returns:
            Model document if found, otherwise None.
        """
        return self.collection.find_one({"model_name": model_name})

    # ---------------------------------------------------------------------
    # Async Wrappers (For FastAPI / Async Services)
    # ---------------------------------------------------------------------

    async def get_all_models_async(self) -> List[Dict[str, Any]]:
        """Async wrapper for get_all_models."""
        return await run_in_threadpool(self.get_all_models)

    async def find_models_async(
        self, filter: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Async wrapper for find_models."""
        return await run_in_threadpool(self.find_models, filter)

    async def get_model_by_name_async(
        self, model_name: str
    ) -> Optional[Dict[str, Any]]:
        """Async wrapper for get_model_by_name."""
        return await run_in_threadpool(self.get_model_by_name, model_name)