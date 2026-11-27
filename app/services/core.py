from app.db import get_db

def fleet_summary():
    db = get_db()
    vehicles = db.execute("SELECT * FROM vehicles ORDER BY id").fetchall()
    chargers = db.execute("SELECT * FROM chargers ORDER BY id").fetchall()
    assignments = db.execute("SELECT * FROM assignments ORDER BY id").fetchall()
    return {
        "vehicles": vehicles,
        "chargers": chargers,
        "assignments": assignments,
        "vehicle_count": len(vehicles),
        "available": sum(v["status"] == "Available" for v in vehicles),
        "charging": sum(v["status"] == "Charging" for v in vehicles),
        "low_battery": sum(v["soc"] < 25 for v in vehicles),
        "charger_count": len(chargers),
    }

def energy_estimate(distance_km, consumption_kwh_per_100km):
    return distance_km * consumption_kwh_per_100km / 100

def remaining_range(battery_kwh, soc_percent, consumption):
    if consumption <= 0:
        raise ValueError("Consumption must be greater than zero.")
    usable = battery_kwh * soc_percent / 100
    return usable / consumption * 100

def simulate_recovery(disruption_kind, target):
    db = get_db()
    db.execute("INSERT INTO disruptions(kind,target,severity) VALUES (?,?,?)",
               (disruption_kind, target, "High"))
    db.commit()

    vehicles = db.execute("SELECT * FROM vehicles ORDER BY soc DESC").fetchall()
    candidates = [
        v for v in vehicles
        if v["status"] in ("Available", "Charging")
        and v["soc"] >= 35
    ]
    if candidates:
        chosen = candidates[0]
        proposal = {
            "status": "PROPOSED",
            "vehicle": chosen["name"],
            "reason": "Highest available state of charge among eligible demo vehicles.",
            "checks": [
                "Vehicle is marked available or charging",
                "State of charge is at least 35%",
                "Proposal is a demonstration heuristic, not a live dispatch"
            ]
        }
    else:
        proposal = {
            "status": "NO_FEASIBLE_DEMO_OPTION",
            "vehicle": None,
            "reason": "No vehicle met the demonstration eligibility rules.",
            "checks": [
                "No eligible vehicle found",
                "Original commitment should be flagged for human review"
            ]
        }
    return proposal
