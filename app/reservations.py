"""Database foundation for UrbanRoute ChargeReserve.

Reservations use ISO-8601 timestamps. Active reservations are protected
against overlapping bookings by SQLite triggers, not only application code.
"""

from app.db import get_db


ACTIVE_RESERVATION_STATUSES = ("confirmed", "checked_in", "charging")


def initialize_reservation_schema():
    db = get_db()

    vehicle_columns = {
        row["name"]
        for row in db.execute("PRAGMA table_info(vehicles)").fetchall()
    }
    if "connector_type" not in vehicle_columns:
        db.execute(
            "ALTER TABLE vehicles "
            "ADD COLUMN connector_type TEXT NOT NULL DEFAULT 'CCS2'"
        )

    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS charger_ports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            charger_id INTEGER NOT NULL,
            port_number TEXT NOT NULL,
            connector_type TEXT NOT NULL DEFAULT 'CCS2',
            max_power_kw REAL NOT NULL DEFAULT 60,
            status TEXT NOT NULL DEFAULT 'Available',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (charger_id) REFERENCES chargers(id),
            UNIQUE (charger_id, port_number)
        );

        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id INTEGER NOT NULL,
            port_id INTEGER NOT NULL,
            start_at TEXT NOT NULL,
            end_at TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'confirmed',
            energy_target_kwh REAL NOT NULL DEFAULT 0,
            estimated_cost REAL NOT NULL DEFAULT 0,
            notes TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vehicle_id) REFERENCES vehicles(id),
            FOREIGN KEY (port_id) REFERENCES charger_ports(id),
            CHECK (end_at > start_at),
            CHECK (energy_target_kwh >= 0),
            CHECK (estimated_cost >= 0)
        );

        CREATE TABLE IF NOT EXISTS charging_waitlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id INTEGER NOT NULL,
            charger_id INTEGER NOT NULL,
            requested_energy_kwh REAL NOT NULL DEFAULT 0,
            priority_score REAL NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'waiting',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vehicle_id) REFERENCES vehicles(id),
            FOREIGN KEY (charger_id) REFERENCES chargers(id),
            CHECK (requested_energy_kwh >= 0)
        );

        CREATE INDEX IF NOT EXISTS idx_reservations_port_time
            ON reservations(port_id, start_at, end_at, status);

        CREATE INDEX IF NOT EXISTS idx_reservations_vehicle_time
            ON reservations(vehicle_id, start_at, end_at, status);

        CREATE INDEX IF NOT EXISTS idx_waitlist_charger_status
            ON charging_waitlist(charger_id, status, priority_score DESC);

        CREATE TRIGGER IF NOT EXISTS prevent_reservation_overlap_insert
        BEFORE INSERT ON reservations
        WHEN NEW.status IN ('confirmed', 'checked_in', 'charging')
        BEGIN
            SELECT CASE WHEN EXISTS (
                SELECT 1
                FROM reservations existing
                WHERE existing.status IN ('confirmed', 'checked_in', 'charging')
                  AND julianday(existing.start_at) < julianday(NEW.end_at)
                  AND julianday(existing.end_at) > julianday(NEW.start_at)
                  AND (
                      existing.port_id = NEW.port_id
                      OR existing.vehicle_id = NEW.vehicle_id
                  )
            )
            THEN RAISE(ABORT, 'Reservation overlaps an existing booking')
            END;
        END;

        CREATE TRIGGER IF NOT EXISTS prevent_reservation_overlap_update
        BEFORE UPDATE OF vehicle_id, port_id, start_at, end_at, status
        ON reservations
        WHEN NEW.status IN ('confirmed', 'checked_in', 'charging')
        BEGIN
            SELECT CASE WHEN EXISTS (
                SELECT 1
                FROM reservations existing
                WHERE existing.id != NEW.id
                  AND existing.status IN ('confirmed', 'checked_in', 'charging')
                  AND julianday(existing.start_at) < julianday(NEW.end_at)
                  AND julianday(existing.end_at) > julianday(NEW.start_at)
                  AND (
                      existing.port_id = NEW.port_id
                      OR existing.vehicle_id = NEW.vehicle_id
                  )
            )
            THEN RAISE(ABORT, 'Reservation overlaps an existing booking')
            END;
        END;
        """
    )

    # Create two demonstration ports per station. Existing ports are retained.
    chargers = db.execute(
        "SELECT id, power_kw, status FROM chargers ORDER BY id"
    ).fetchall()

    for charger in chargers:
        station_status = str(charger["status"]).lower()
        port_status = (
            "Out of service"
            if "out" in station_status or "maintenance" in station_status
            else "Available"
        )
        power = float(charger["power_kw"])
        for port_number in ("A", "B"):
            db.execute(
                """
                INSERT OR IGNORE INTO charger_ports
                    (charger_id, port_number, connector_type, max_power_kw, status)
                VALUES (?, ?, 'CCS2', ?, ?)
                """,
                (charger["id"], port_number, power, port_status),
            )

    db.commit()
