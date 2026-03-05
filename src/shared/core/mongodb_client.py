from pymongo import MongoClient
from src.shared.config.settings import settings
from src.shared.utils.logger import get_logger

logger = get_logger(__name__)


class MongoDBClient:
    """
    Client for USECASE SESSIONS DB
    (Now using remote Atlas instead of local MongoDB)
    """

    def __init__(self, uri=None, db_name=None, collection=None):
        self.uri = uri or settings.MONGODB_URI
        self.db_name = db_name or settings.MONGODB_DB
        self.collection_name = collection or settings.MONGODB_COLLECTION

        logger.info(
            "Connecting to Usecase MongoDB",
            uri=self.uri,
            db=self.db_name,
            collection=self.collection_name
        )

        # SRV and multi-host URIs → NO directConnection flag
        if self.uri.startswith("mongodb+srv://") or "," in self.uri:
            self.client = MongoClient(self.uri)
        else:
            self.client = MongoClient(self.uri, directConnection=True)

        self.db = self.client[self.db_name]
        self.collection = self.db[self.collection_name]

    # === SYNC ===
    def insert_one(self, data):
        return self.collection.insert_one(data)

    # === ASYNC WRAPPERS ===
    async def find_one(self, query):
        return self.collection.find_one(query)

    async def update_one(self, query, update):
        return self.collection.update_one(query, update)

    async def find_many(self, query=None, projection=None):
        cursor = self.collection.find(query or {}, projection)
        return list(cursor)
