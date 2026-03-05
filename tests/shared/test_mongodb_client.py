# tests/shared/test_mongodb_client.py
import pytest
from src.shared.core.mongodb_client import MongoDBClient

def test_mongodb_client_connect(monkeypatch):
    # monkeypatch MongoClient to avoid requiring a real DB
    class DummyClient:
        def __init__(self, uri, serverSelectionTimeoutMS=None):
            pass
        @property
        def admin(self):
            class Admin:
                def command(self, x):
                    return {"ok": 1}
            return Admin()
        def __getitem__(self, name):
            class DB:
                def __init__(self):
                    self._collections = {}
                def __getitem__(self, n):
                    return self._collections.setdefault(n, [])
            return DB()

    monkeypatch.setattr("src.shared.core.mongodb_client.MongoClient", DummyClient)
    client = MongoDBClient(uri="mongodb://dummy:27017", db_name="test_db")
    client.connect()
    assert client._db is not None
