import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-development-secret")
    DEBUG = os.environ.get("FLASK_DEBUG", "true").lower() == "true"
    DATABASE = str(BASE_DIR / "instance" / "urbanroute.db")
