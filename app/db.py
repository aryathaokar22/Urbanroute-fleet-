import sqlite3
from flask import current_app, g
from pathlib import Path

def get_db():
    if "db" not in g:
        Path(current_app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_app(app):
    app.teardown_appcontext(close_db)
    with app.app_context():
        db = get_db()
        db.executescript("""
        CREATE TABLE IF NOT EXISTS vehicles (
            id INTEGER PRIMARY KEY, name TEXT NOT NULL, model TEXT NOT NULL,
            battery_kwh REAL NOT NULL, soc REAL NOT NULL,
            consumption REAL NOT NULL, status TEXT NOT NULL, location TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS chargers (
            id INTEGER PRIMARY KEY, name TEXT NOT NULL, location TEXT NOT NULL,
            power_kw REAL NOT NULL, status TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS assignments (
            id INTEGER PRIMARY KEY, title TEXT NOT NULL, vehicle_id INTEGER,
            destination TEXT NOT NULL, energy_required REAL NOT NULL,
            deadline TEXT NOT NULL, status TEXT NOT NULL,
            FOREIGN KEY(vehicle_id) REFERENCES vehicles(id)
        );
        CREATE TABLE IF NOT EXISTS disruptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT NOT NULL,
            target TEXT NOT NULL, severity TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """)

def seed_database():
    db = get_db()
    if db.execute("SELECT COUNT(*) FROM vehicles").fetchone()[0] == 0:
        db.executemany("""INSERT INTO vehicles
            (id,name,model,battery_kwh,soc,consumption,status,location)
            VALUES (?,?,?,?,?,?,?,?)""", [
            (1,"UR-001","Electric Van",75,82,19.5,"Available","Whitefield Depot"),
            (2,"UR-002","Electric Van",75,46,20.2,"On assignment","Marathahalli"),
            (3,"UR-003","Electric Cargo","95",31,24.0,"Charging","KR Puram Hub"),
            (4,"UR-004","Electric Mini Truck",120,91,28.0,"Available","Whitefield Depot"),
            (5,"UR-005","Electric Van",75,18,21.0,"Needs charging","Indiranagar"),
            (6,"UR-006","Electric Cargo",95,67,23.0,"Available","Whitefield Depot"),
        ])
        db.executemany("""INSERT INTO chargers (id,name,location,power_kw,status)
            VALUES (?,?,?,?,?)""", [
            (1,"WHF-CH-01","Whitefield Depot",60,"Available"),
            (2,"KRH-CH-02","KR Puram Hub",120,"Occupied"),
            (3,"MAR-CH-03","Marathahalli",60,"Available"),
            (4,"IND-CH-04","Indiranagar",30,"Out of service"),
        ])
        db.executemany("""INSERT INTO assignments
            (id,title,vehicle_id,destination,energy_required,deadline,status)
            VALUES (?,?,?,?,?,?,?)""", [
            (1,"Retail delivery route",2,"Marathahalli",18,"14:30","In progress"),
            (2,"Warehouse replenishment",4,"Electronic City",32,"16:00","Scheduled"),
            (3,"Express parcel route",6,"Indiranagar",21,"15:15","Scheduled"),
        ])
        db.commit()
