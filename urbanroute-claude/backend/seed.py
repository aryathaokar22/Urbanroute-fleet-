"""Sample data, mirrors the front end so the app is never empty on first run."""
from datetime import datetime, timedelta, timezone
from engine import iso


def make_seed():
    now = datetime.now(timezone.utc)
    t = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    veh = [
        {"id": "UR-101", "name": "Tata Ace EV", "kwh": 21.3, "cons": .14, "pct": 82, "conn": "CCS2", "status": "Available", "lat": 12.935, "lng": 77.614},
        {"id": "UR-102", "name": "Mahindra eSupro", "kwh": 15, "cons": .13, "pct": 24, "conn": "CCS2", "status": "Available", "lat": 12.97, "lng": 77.64},
        {"id": "UR-103", "name": "Eicher Pro X", "kwh": 70, "cons": .35, "pct": 55, "conn": "CCS2", "status": "On route", "lat": 12.99, "lng": 77.55},
        {"id": "UR-104", "name": "Piaggio Ape E-Xtra", "kwh": 7.4, "cons": .09, "pct": 18, "conn": "Type 2", "status": "Available", "lat": 12.91, "lng": 77.6},
        {"id": "UR-105", "name": "Tata Ace EV 2", "kwh": 21.3, "cons": .14, "pct": 91, "conn": "CCS2", "status": "Available", "lat": 12.95, "lng": 77.7},
        {"id": "UR-106", "name": "Mahindra Treo Zor", "kwh": 7.4, "cons": .1, "pct": 35, "conn": "Type 2", "status": "Charging", "lat": 12.88, "lng": 77.63},
        {"id": "UR-107", "name": "Eicher Pro X 2", "kwh": 70, "cons": .35, "pct": 12, "conn": "CCS2", "status": "Offline", "lat": 13.03, "lng": 77.59},
        {"id": "UR-108", "name": "Tata Ace EV 3", "kwh": 21.3, "cons": .14, "pct": 64, "conn": "CCS2", "status": "Available", "lat": 12.92, "lng": 77.67}]
    sta = [
        {"id": "ST-1", "name": "Koramangala Hub", "conn": "CCS2", "kw": 50, "n": 4, "price": 11, "lat": 12.934, "lng": 77.622},
        {"id": "ST-2", "name": "Whitefield Depot", "conn": "CCS2", "kw": 60, "n": 3, "price": 10, "lat": 12.969, "lng": 77.75},
        {"id": "ST-3", "name": "Indiranagar Fast", "conn": "CCS2", "kw": 120, "n": 2, "price": 19, "lat": 12.978, "lng": 77.64},
        {"id": "ST-4", "name": "HSR Layout Point", "conn": "Type 2", "kw": 22, "n": 3, "price": 12, "lat": 12.912, "lng": 77.64},
        {"id": "ST-5", "name": "Hebbal Plaza", "conn": "CCS2", "kw": 50, "n": 2, "price": 21, "lat": 13.035, "lng": 77.597},
        {"id": "ST-6", "name": "Jayanagar Type 2", "conn": "Type 2", "kw": 22, "n": 2, "price": 12, "lat": 12.925, "lng": 77.583}]
    day = lambda n: iso(now - timedelta(days=n))
    return {
        "veh": veh, "sta": sta,
        "ses": [{"id": "CS-1", "vid": "UR-106", "sid": "ST-4", "start": iso(t), "target": 90, "mins": 150, "status": "Scheduled"}],
        "rou": [{"id": "RT-1", "name": "North loop deliveries", "vid": "UR-105",
                 "stops": [{"n": "Depot", "km": 0}, {"n": "Hebbal drop", "km": 24}, {"n": "Yelahanka drop", "km": 12}, {"n": "Return", "km": 30}],
                 "km": 66, "kwh": 9.2, "stop": None, "status": "Planned", "at": iso(now)}],
        "res": [{"id": "RS-1", "vid": "UR-101", "sid": "ST-1", "cn": "1", "start": iso(t + timedelta(hours=1)), "end": iso(t + timedelta(hours=2)), "status": "Confirmed"}],
        "pas": {v["id"]: {"id": "FP-" + v["id"][3:], "vid": v["id"], "status": "Active", "plan": "Annual (demo)", "bal": 2000} for v in veh},
        "txn": [],
        "own": {"car": {"name": "Tata Nexon EV", "kwh": 40.5, "cons": .15, "pct": 58, "conn": "CCS2", "tariff": 7, "lat": 12.935, "lng": 77.614},
                "log": [{"id": "L1", "at": day(12), "place": "Home", "kwh": 18, "cost": 126, "type": "Home"},
                        {"id": "L2", "at": day(8), "place": "Koramangala Hub", "kwh": 22, "cost": 242, "type": "Public"},
                        {"id": "L3", "at": day(3), "place": "Home", "kwh": 15, "cost": 105, "type": "Home"}]},
    }
