import os


class Config:
    """Base configuration."""

    DEBUG = False
    SECRET_KEY = os.environ.get("APP_SECRET", "REDACTED")
    SQLALCHEMY_TRACK_MODIFICATIONS = True
