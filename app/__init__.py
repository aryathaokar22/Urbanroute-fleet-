from flask import Flask
from config import Config


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)

    if test_config:
        app.config.update(test_config)

    from app.db import init_app, seed_database
    from app.reservations import initialize_reservation_schema
    from app.routes import register_routes
    from app.charging_pages import register_charging_pages

    init_app(app)

    with app.app_context():
        seed_database()
        initialize_reservation_schema()

    register_routes(app)
    register_charging_pages(app)

    return app
