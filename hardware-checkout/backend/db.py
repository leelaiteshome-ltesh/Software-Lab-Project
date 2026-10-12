import os

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

_client = None


def get_database():
    """Connect to MongoDB Atlas once and reuse the connection."""
    global _client
    if _client is None:
        uri = os.getenv("MONGODB_URI")
        if not uri:
            raise RuntimeError("MONGODB_URI is missing. Add it to backend/.env")
        _client = MongoClient(uri)
    return _client[os.getenv("MONGODB_DB_NAME", "hardware_checkout")]
