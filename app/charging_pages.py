from flask import render_template

from app.db import get_db


def register_charging_pages(app):
    @app.get("/dashboard/reservations")
    def reservations():
        db = get_db()
        vehicles = db.execute(
            "SELECT id, name, model, soc, connector_type FROM vehicles ORDER BY id"
        ).fetchall()

        return render_template(
            "dashboard/reservations.html",
            vehicles=vehicles,
        )
