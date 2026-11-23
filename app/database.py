
import sqlite3
import os
from flask import g, current_app


def get_db():
    if "db" not in g:
        database_path = current_app.config["DATABASE"]

        os.makedirs(
            os.path.dirname(database_path),
            exist_ok=True
        )

        g.db = sqlite3.connect(database_path)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")

    return g.db


def close_db(error=None):
    db = g.pop("db", None)

    if db is not None:
        db.close()


def initialize_database(app):
    app.teardown_appcontext(close_db)

    with app.app_context():
        db = get_db()

        db.executescript("""
            CREATE TABLE IF NOT EXISTS vehicles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                model TEXT NOT NULL,
                battery_capacity REAL NOT NULL,
                battery_level REAL NOT NULL,
                consumption REAL NOT NULL,
                status TEXT NOT NULL,
                location TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS chargers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                location TEXT NOT NULL,
                power REAL NOT NULL,
                status TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                vehicle_id INTEGER,
                destination TEXT NOT NULL,
                energy_required REAL NOT NULL,
                deadline TEXT NOT NULL,
                status TEXT NOT NULL,
                FOREIGN KEY (vehicle_id) REFERENCES vehicles(id)
            );

            CREATE TABLE IF NOT EXISTS disruptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                target TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        from instance.data.seed_data import seed_database

        seed_database(db)
        db.commit()
