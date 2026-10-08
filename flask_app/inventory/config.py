"""
Configuration for the Flask Inventory Management System.

Values can be overridden with environment variables (optionally via a .env
file, which is read by python-decouple).
"""

from pathlib import Path

from decouple import Csv, config

# flask_app/ directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Absolute path to the SQLite database (kept separate from the Django db.sqlite3)
_DEFAULT_DB = (BASE_DIR / "inventory.db").as_posix()


class Config:
    """Default configuration used for local development."""

    SECRET_KEY = config(
        "SECRET_KEY",
        default="flask-inventory-secret-key-change-in-production-2024",
    )
    DEBUG = config("DEBUG", default=True, cast=bool)

    # Only applied when explicitly provided; Flask allows any host otherwise.
    _allowed = config("ALLOWED_HOSTS", default="", cast=Csv())
    ALLOWED_HOSTS = _allowed or None

    SQLALCHEMY_DATABASE_URI = config(
        "DATABASE_URL", default=f"sqlite:///{_DEFAULT_DB}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    # Threshold used for "low stock" alerts
    LOW_STOCK_THRESHOLD = config("LOW_STOCK_THRESHOLD", default=10, cast=int)

    # Development server port
    PORT = config("PORT", default=5000, cast=int)
