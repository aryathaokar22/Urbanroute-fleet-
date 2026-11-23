
from flask import render_template, request, jsonify
from app.database import get_db


def register_routes(app):

    @app.route("/")
    def home():
        return render_template("index.html")

    @app.route("/dashboard")
    def dashboard():
        db = get_db()

        vehicles = db.execute(
            "SELECT * FROM vehicles"
        ).fetchall()

        chargers = db.execute(
            "SELECT * FROM chargers"
        ).fetchall()

        assignments = db.execute(
            "SELECT * FROM assignments"
        ).fetchall()

        return render_template(
            "dashboard/overview.html",
            vehicles=vehicles,
            chargers=chargers,
            assignments=assignments
        )

    @app.route("/dashboard/vehicles")
    def vehicle_page():
        db = get_db()
        vehicles = db.execute(
            "SELECT * FROM vehicles"
        ).fetchall()

        return render_template(
            "dashboard/vehicles.html",
            vehicles=vehicles
        )

    @app.route("/dashboard/chargers")
    def charger_page():
        db = get_db()
        chargers = db.execute(
            "SELECT * FROM chargers"
        ).fetchall()

        return render_template(
            "dashboard/chargers.html",
            chargers=chargers
        )

    @app.route("/dashboard/assignments")
    def assignment_page():
        db = get_db()
        assignments = db.execute(
            "SELECT * FROM assignments"
        ).fetchall()

        return render_template(
            "dashboard/assignments.html",
            assignments=assignments
        )

    @app.route("/api/energy", methods=["GET", "POST"])
    def energy():
        data = request.get_json(silent=True) or request.values

        try:
            distance = float(data.get("distance", 100))
            consumption = float(data.get("consumption", 20))

            if distance < 0 or consumption <= 0:
                raise ValueError

        except (ValueError, TypeError):
            return jsonify({"error": "Invalid input"}), 400

        return jsonify({
            "distance_km": distance,
            "energy_required_kwh": round(
                distance * consumption / 100, 2
            )
        })

    @app.route("/api/range", methods=["GET", "POST"])
    def range_calculation():
        data = request.get_json(silent=True) or request.values

        try:
            battery = float(data.get("battery", 75))
            level = float(data.get("level", 50))
            consumption = float(data.get("consumption", 20))

            if (
                battery <= 0
                or consumption <= 0
                or not 0 <= level <= 100
            ):
                raise ValueError

        except (ValueError, TypeError):
            return jsonify({"error": "Invalid input"}), 400

        available_energy = battery * level / 100
        estimated_range = available_energy / consumption * 100

        return jsonify({
            "estimated_range_km": round(estimated_range, 2)
        })

    @app.route("/api/disruption", methods=["POST"])
    def disruption():
        data = request.get_json(silent=True) or {}

        kind = data.get("type", "Vehicle Breakdown")
        target = data.get("target", "UR-001")

        db = get_db()

        db.execute(
            "INSERT INTO disruptions (type, target) VALUES (?, ?)",
            (kind, target)
        )
        db.commit()

        candidates = db.execute("""
            SELECT * FROM vehicles
            WHERE status = 'Available'
              AND battery_level >= 35
              AND name != ?
            ORDER BY battery_level DESC
        """, (target,)).fetchall()

        if candidates:
            selected = candidates[0]

            return jsonify({
                "status": "Recovery Candidate Found",
                "vehicle": selected["name"],
                "battery": selected["battery_level"],
                "message": "Eligible replacement identified using demo rules."
            })

        return jsonify({
            "status": "No Feasible Candidate",
            "message": "Human intervention is required."
        })
