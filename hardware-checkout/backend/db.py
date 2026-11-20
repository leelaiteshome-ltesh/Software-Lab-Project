import os

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

# Each database gets its own MongoDB connection (its own MongoClient), so the
# users, projects and hardware databases are fully independent and any one of
# them can be moved to a different cluster by changing only its URI.
#
#   database   URI setting (falls back to MONGODB_URI)   name setting
#   users      MONGODB_USERS_URI                         MONGODB_DB_NAME
#   projects   MONGODB_PROJECTS_URI                      MONGODB_PROJECTS_DB_NAME
#   hardware   MONGODB_HARDWARE_URI                      MONGODB_HARDWARE_DB_NAME

_clients = {}


def _get_client(uri_setting):
    """Open this database's connection once and reuse it."""
    if uri_setting not in _clients:
        uri = os.getenv(uri_setting) or os.getenv("MONGODB_URI")
        if not uri:
            raise RuntimeError(f"{uri_setting} (or MONGODB_URI) is missing. Add it to backend/.env")
        _clients[uri_setting] = MongoClient(uri)
    return _clients[uri_setting]


def get_database():
    """Users database, on its own connection."""
    return _get_client("MONGODB_USERS_URI")[os.getenv("MONGODB_DB_NAME", "hardware_checkout")]


def get_projects_database():
    """Projects database, on its own connection."""
    return _get_client("MONGODB_PROJECTS_URI")[os.getenv("MONGODB_PROJECTS_DB_NAME", "hardware_checkout_projects")]


def get_hardware_database():
    """Hardware sets and per-project checkouts, on a third connection."""
    return _get_client("MONGODB_HARDWARE_URI")[os.getenv("MONGODB_HARDWARE_DB_NAME", "hardware_checkout_hardware")]
