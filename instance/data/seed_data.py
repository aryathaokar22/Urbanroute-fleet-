
def seed_database(db):
    """
    Insert demonstration data into the database.
    Existing records are preserved.
    """

    vehicle_count = db.execute(
        "SELECT COUNT(*) FROM vehicles"
    ).fetchone()[0]

    if vehicle_count == 0:
        vehicles = [
            ("UR-001", "Tata Nexon EV", 40.5, 85, 15, "Available", "Whitefield"),
            ("UR-002", "MG ZS EV", 50.3, 65, 17, "Charging", "Indiranagar"),
            ("UR-003", "Tata Tiago EV", 24, 92, 12, "Available", "Electronic City"),
            ("UR-004", "BYD Atto 3", 60.5, 45, 16, "In Service", "Marathahalli"),
            ("UR-005", "Hyundai Kona EV", 39.2, 28, 14, "Available", "Hebbal"),
            ("UR-006", "Mahindra XUV400", 39.4, 70, 15, "Available", "Koramangala")
        ]

        db.executemany("""
            INSERT INTO vehicles (
                name, model, battery_capacity, battery_level,
                consumption, status, location
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, vehicles)

    charger_count = db.execute(
        "SELECT COUNT(*) FROM chargers"
    ).fetchone()[0]

    if charger_count == 0:
        chargers = [
            ("CH-001", "Whitefield", 60, "Available"),
            ("CH-002", "Indiranagar", 30, "Occupied"),
            ("CH-003", "Electronic City", 120, "Available"),
            ("CH-004", "Marathahalli", 60, "Out of Service")
        ]

        db.executemany("""
            INSERT INTO chargers (name, location, power, status)
            VALUES (?, ?, ?, ?)
        """, chargers)

    assignment_count = db.execute(
        "SELECT COUNT(*) FROM assignments"
    ).fetchone()[0]

    if assignment_count == 0:
        vehicle_ids = {
            row["name"]: row["id"]
            for row in db.execute(
                "SELECT id, name FROM vehicles"
            ).fetchall()
        }

        assignments = [
            ("Delivery Route A", vehicle_ids.get("UR-004"), "Whitefield", 18, "2026-11-23 14:00", "In Progress"),
            ("Delivery Route B", vehicle_ids.get("UR-001"), "Indiranagar", 12, "2026-11-23 16:00", "Pending"),
            ("Delivery Route C", vehicle_ids.get("UR-003"), "Electronic City", 20, "2026-11-23 18:00", "Completed")
        ]

        db.executemany("""
            INSERT INTO assignments (
                title, vehicle_id, destination, energy_required,
                deadline, status
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, assignments)

    db.commit()
