import os

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

_client = None


def _get_client():
    """Connect to MongoDB Atlas once and reuse the connection."""
    global _client
    if _client is None:
        uri = os.getenv("MONGODB_URI")
        if not uri:
            raise RuntimeError("MONGODB_URI is missing. Add it to backend/.env")
        _client = MongoClient(uri)
    return _client


def get_database():
    """Users database."""
    return _get_client()[os.getenv("MONGODB_DB_NAME", "hardware_checkout")]


def get_projects_database():
    """Projects live in their own database so they can scale (or move to
    their own cluster) independently of users."""
    return _get_client()[os.getenv("MONGODB_PROJECTS_DB_NAME", "hardware_checkout_projects")]


def get_hardware_database():
    """Hardware sets and per-project checkouts live in their own database."""
    return _get_client()[os.getenv("MONGODB_HARDWARE_DB_NAME", "hardware_checkout_hardware")]
