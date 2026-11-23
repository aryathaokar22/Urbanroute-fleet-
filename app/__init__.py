from flask import Flask
from config import Config


def create_app(test_config=None):
    app = Flask(__name__)

    app.config.from_object(Config)

    if test_config:
        app.config.update(test_config)

    from app.database import initialize_database
    from app.routes import register_routes

    initialize_database(app)
    register_routes(app)

    return app
