
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "urbanroute-development-secret-key"
    )

    DEBUG = True

    DATABASE = os.path.join(
        BASE_DIR,
        "instance",
        "urbanroute.db"
    )

    JSON_SORT_KEYS = False
