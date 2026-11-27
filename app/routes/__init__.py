import math

from flask import (
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
)

from app.db import get_db
from app.services.core import (
    fleet_summary,
    energy_estimate,
    remaining_range,
    simulate_recovery,
)


def register_routes(app):

    @app.route("/")
    def home():
        return render_template("public/index.html")

    @app.route("/solutions")
    def solutions():
        return render_template("public/solutions.html")

    @app.route("/platform")
    def platform():
        return render_template("public/platform.html")

    @app.route("/innovation")
    def innovation():
        return render_template("public/innovation.html")

    @app.route("/about")
    def about():
        return render_template("public/about.html")

    @app.route("/contact", methods=["GET", "POST"])
    def contact():
        if request.method == "POST":
            flash(
                "Thanks. This demo form is not connected to email delivery.",
                "success",
            )
            return redirect(url_for("contact"))

        return render_template("public/contact.html")

    @app.route("/dashboard")
    def dashboard():
        return render_template(
            "dashboard/overview.html",
            data=fleet_summary(),
        )

    @app.route("/dashboard/vehicles")
    def vehicles():
        return render_template(
            "dashboard/vehicles.html",
            data=fleet_summary(),
        )

    @app.route("/dashboard/chargers")
    def chargers():
        return render_template(
            "dashboard/chargers.html",
            data=fleet_summary(),
        )

    @app.route("/dashboard/assignments")
    def assignments():
        return render_template(
            "dashboard/assignments.html",
            data=fleet_summary(),
        )

    @app.route("/dashboard/resilience")
    def resilience():
        rows = get_db().execute(
            "SELECT * FROM disruptions ORDER BY id DESC"
        ).fetchall()

        return render_template(
            "dashboard/resilience.html",
            disruptions=rows,
        )

    @app.route("/api/energy", methods=["GET", "POST"])
    def api_energy():
        payload = request.get_json(silent=True) or request.args

        try:
            distance = float(
                payload.get("distance_km", payload.get("distance", 100))
            )
            consumption = float(payload.get("consumption", 20))

            if (
                not math.isfinite(distance)
                or not math.isfinite(consumption)
                or distance < 0
                or consumption <= 0
            ):
                raise ValueError

            result = round(
                energy_estimate(distance, consumption), 2
            )

            return jsonify({
                "distance_km": distance,
                "energy_kwh": result,
                "energy_required_kwh": result,
            })

        except (TypeError, ValueError, OverflowError):
            return jsonify({
                "error": (
                    "Provide a non-negative distance and "
                    "positive consumption."
                )
            }), 400

    @app.route("/api/range", methods=["GET", "POST"])
    def api_range():
        payload = request.get_json(silent=True) or request.args

        try:
            battery = float(
                payload.get("battery_kwh", payload.get("battery", 75))
            )
            soc = float(
                payload.get("soc", payload.get("level", 50))
            )
            consumption = float(payload.get("consumption", 20))

            if (
                not all(math.isfinite(value) for value in (
                    battery, soc, consumption
                ))
                or battery <= 0
                or not 0 <= soc <= 100
                or consumption <= 0
            ):
                raise ValueError

            result = round(
                remaining_range(battery, soc, consumption), 2
            )

            return jsonify({
                "estimated_range_km": result,
            })

        except (TypeError, ValueError, OverflowError):
            return jsonify({
                "error": (
                    "Check battery capacity, SoC (0-100), "
                    "and positive consumption."
                )
            }), 400

    @app.route("/api/disruptions", methods=["GET", "POST"])
    def api_disruptions():
        if request.method == "GET":
            rows = get_db().execute(
                "SELECT * FROM disruptions ORDER BY id DESC"
            ).fetchall()

            return jsonify([dict(row) for row in rows])

        payload = request.get_json(silent=True) or {}

        kind = str(
            payload.get("kind", "Vehicle unavailable")
        ).strip()[:80]

        target = str(
            payload.get("target", "UR-001")
        ).strip()[:80]

        if not kind or not target:
            return jsonify({
                "error": "Disruption kind and target are required."
            }), 400

        return jsonify(simulate_recovery(kind, target))

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("errors/404.html"), 404
