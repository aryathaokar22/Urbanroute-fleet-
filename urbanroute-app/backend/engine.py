"""UrbanRoute Fleet engine: range, energy, charging, station ranking, coordination.

Simplified models (see README): constant consumption and charging power,
no traffic, weather or charge taper. Station estimates are SIMULATED.
"""
import math
from datetime import datetime, timedelta, timezone

RESERVE = 0.10  # keep 10% battery on arrival


def parse(ts):
    return datetime.fromisoformat(str(ts).replace("Z", "+00:00"))


def iso(dt):
    return dt.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def range_km(v):
    return v["kwh"] * v["pct"] / 100 / v["cons"]


def calc_route(stops, v):
    """Distance, energy, arrival battery and per-leg battery for a route."""
    avail = v["kwh"] * v["pct"] / 100
    cum, legs = 0.0, []
    for s in stops:
        cum += s["km"]
        left = (avail - cum * v["cons"]) / v["kwh"] * 100
        legs.append({"name": s["n"], "km": s["km"], "kwh": s["km"] * v["cons"],
                     "battery_after": left, "ok": left >= 10})
    energy = cum * v["cons"]
    short = max(0.0, energy + v["kwh"] * RESERVE - avail)
    return {"km": cum, "kwh": energy, "arrival_pct": (avail - energy) / v["kwh"] * 100,
            "ok": short == 0, "short_kwh": short, "legs": legs}


def haversine(a, b, c, d):
    r = 6371
    x, y = math.radians(c - a), math.radians(d - b)
    q = math.sin(x / 2) ** 2 + math.cos(math.radians(a)) * math.cos(math.radians(c)) * math.sin(y / 2) ** 2
    return 2 * r * math.asin(math.sqrt(q))


def estimate(st, now=None):
    """SIMULATED station estimate, stable for each 10 minute bucket."""
    now = now or datetime.now(timezone.utc)
    bucket = int(now.timestamp() * 1000 // 600000)
    h = 0
    for ch in st["id"] + str(bucket):
        h = (h * 31 + ord(ch)) % 9973
    free = h % (st["n"] + 1)
    return {"free_connectors": free, "wait_minutes": 0 if free else 8 + h % 22,
            "working_probability": 84 + h % 15, "available_at_arrival": free > 0 or h % 3 > 0,
            "updated_at": iso(datetime.fromtimestamp(bucket * 600, timezone.utc)),
            "source": "simulated", "is_simulated": True}


def rank_stations(v, stations, radius, now=None):
    out = []
    for s in stations:
        if s["conn"] != v["conn"]:
            continue
        d = haversine(v["lat"], v["lng"], s["lat"], s["lng"])
        if d > radius:
            continue
        e = estimate(s, now)
        out.append({"station": s, "distance_km": d, "estimate": e,
                    "score": d * 1.5 + e["wait_minutes"] + (100 - e["working_probability"]) * .5})
    out.sort(key=lambda x: x["score"])
    for i, x in enumerate(out):
        x["role"] = "primary" if i == 0 else "backup" if i == 1 else "option"
    return out


def charge_minutes(v, st, frm, to):
    return math.ceil((to - frm) / 100 * v["kwh"] / st["kw"] * 60)


def overlap(a, b, c, d):
    return a < d and c < b


def _intervals(sid, sessions, reservations, skip=None):
    out = []
    for x in sessions:
        if x["sid"] == sid and x["status"] == "Scheduled" and x["id"] != skip:
            s = parse(x["start"]); out.append((s, s + timedelta(minutes=x["mins"])))
    for x in reservations:
        if x["sid"] == sid and x["status"] == "Confirmed" and x["id"] != skip:
            out.append((parse(x["start"]), parse(x["end"])))
    return out


def load(sid, a, b, sessions, reservations, skip=None):
    return sum(1 for s, e in _intervals(sid, sessions, reservations, skip) if overlap(a, b, s, e))


def next_free(st, a, length, sessions, reservations):
    t = a
    while t < a + timedelta(hours=24):
        if load(st["id"], t, t + length, sessions, reservations) < st["n"]:
            return t
        t += timedelta(minutes=15)
    return None


def max_concurrent(intervals):
    ev = sorted([(s, 1) for s, e in intervals] + [(e, -1) for s, e in intervals], key=lambda x: (x[0], x[1]))
    cur = peak = 0
    for _, d in ev:
        cur += d; peak = max(peak, cur)
    return peak


def coordinate(vehicles, stations, horizon=8):
    """Greedy fleet charging plan by priority, respecting connector capacity per hourly slot."""
    used, out, un = {}, [], []
    key = lambda v: -((100 - v["pct"]) + (30 if v.get("urgent") else 0))
    for v in sorted(vehicles, key=key):
        cs = sorted([s for s in stations if s["conn"] == v["conn"]],
                    key=lambda s: haversine(v["lat"], v["lng"], s["lat"], s["lng"]))
        placed = False
        for h in range(horizon):
            for s in cs:
                if used.get((s["id"], h), 0) < s["n"]:
                    used[(s["id"], h)] = used.get((s["id"], h), 0) + 1
                    out.append({"vehicle": v["id"], "station": s["id"], "hour_offset": h})
                    placed = True; break
            if placed: break
        if not placed:
            un.append(v["id"])
    return {"assignments": out, "unassigned": un}


def briefing(state):
    veh, rou, sta = state["veh"], state["rou"], state["sta"]
    byid = {v["id"]: v for v in veh}
    risk = [r for r in rou if r["status"] == "Planned" and r["vid"] in byid
            and not calc_route(r["stops"], byid[r["vid"]])["ok"]]
    low = [v for v in veh if v["pct"] < 40 and v["status"] not in ("Offline", "Charging")]
    slow = [s for s in sta if estimate(s)["wait_minutes"] >= 15]
    out = []
    if risk: out.append({"severity": "high", "title": f"{len(risk)} planned route(s) may not finish", "routes": [r["id"] for r in risk]})
    if low: out.append({"severity": "high", "title": f"{len(low)} vehicle(s) below 40% battery", "vehicles": [v["id"] for v in low]})
    if slow: out.append({"severity": "medium", "title": f"{len(slow)} station(s) with estimated wait over 15 min (simulated)", "stations": [s["id"] for s in slow]})
    return out


# ---- validation (returns an error message or None) ----
def _num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def check_vehicle(v):
    if not str(v.get("name", "")).strip(): return "Vehicle name is required."
    if not (_num(v.get("kwh")) and v["kwh"] > 0): return "Battery capacity must be greater than 0 kWh."
    if not (_num(v.get("cons")) and v["cons"] > 0): return "Consumption must be greater than 0 kWh per km."
    if not (_num(v.get("pct")) and 0 <= v["pct"] <= 100): return "Charge level must be between 0 and 100%."
    return None


def check_station(s):
    if not str(s.get("name", "")).strip(): return "Station name is required."
    if not (_num(s.get("kw")) and s["kw"] > 0): return "Station power must be greater than 0 kW."
    if not (isinstance(s.get("n"), int) and s["n"] >= 1): return "A station needs at least 1 connector."
    if not (_num(s.get("price")) and s["price"] >= 0): return "Price must be 0 or more."
    return None


def check_route(r):
    if not r.get("stops"): return "A route needs at least one stop."
    for s in r["stops"]:
        if not (_num(s.get("km")) and s["km"] >= 0): return "Stop distances must be 0 km or more."
    return None
