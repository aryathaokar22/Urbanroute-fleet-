"""UrbanRoute Fleet backend (Flask + SQLite).

Run:  python app.py   ->  http://localhost:5000  (also serves the front end)
Roles are sent in the X-Role header. This enforces permissions for the demo
but is NOT real authentication (no login, no passwords).
"""
import json, math, os, sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from flask import Flask, jsonify, request, send_from_directory, g

import engine as E
from seed import make_seed

FM, DP, OW = "Fleet Manager", "Dispatcher", "EV Owner"
KEYS = ("veh", "sta", "ses", "rou", "res", "pas", "txn", "own")
WRITERS = {"veh": (FM, DP), "sta": (FM,), "ses": (FM, DP), "rou": (FM, DP), "res": (FM, DP),
           "pas": (FM, DP), "txn": (FM, DP), "own": (OW,)}
DB_PATH = os.environ.get("URBANROUTE_DB", str(Path(__file__).with_name("urbanroute.db")))
FRONTEND = Path(__file__).resolve().parent.parent / "frontend"

app = Flask(__name__)


# ---------- storage ----------
def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.execute("CREATE TABLE IF NOT EXISTS kv (k TEXT PRIMARY KEY, v TEXT NOT NULL)")
    return g.db


@app.teardown_appcontext
def close_db(_):
    d = g.pop("db", None)
    if d: d.close()


def get(key):
    row = db().execute("SELECT v FROM kv WHERE k=?", (key,)).fetchone()
    if row is None:
        seed_all()
        row = db().execute("SELECT v FROM kv WHERE k=?", (key,)).fetchone()
    return json.loads(row[0])


def put(key, val):
    db().execute("INSERT INTO kv(k,v) VALUES(?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v", (key, json.dumps(val)))
    db().commit()


def seed_all():
    for k, v in make_seed().items():
        put(k, v)


def state():
    return {k: get(k) for k in KEYS}


# ---------- helpers ----------
def role():
    return request.headers.get("X-Role", "")


def err(msg, code=400):
    return jsonify({"error": msg}), code


@app.after_request
def cors(r):
    r.headers["Access-Control-Allow-Origin"] = "*"
    r.headers["Access-Control-Allow-Headers"] = "Content-Type, X-Role"
    r.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, OPTIONS"
    return r


@app.route("/api/<path:_>", methods=["OPTIONS"])
def preflight(_):
    return ("", 204)


# ---------- validation of a full collection before it is saved ----------
def validate(key, val, who):
    old = get(key)
    if key == "veh":
        if not isinstance(val, list): return "Vehicles must be a list.", 400
        if len({v.get("id") for v in val}) != len(val): return "Vehicle IDs must be unique.", 400
        for v in val:
            m = E.check_vehicle(v)
            if m: return m, 400
        if who == DP:  # dispatchers can only change status (for example Charging Scheduled)
            o = {v["id"]: v for v in old}
            for v in val:
                b = o.get(v["id"])
                if b is None or {k: x for k, x in v.items() if k != "status"} != {k: x for k, x in b.items() if k != "status"}:
                    return "Dispatchers cannot add, delete or edit vehicles. Ask a fleet manager.", 403
            if len(val) != len(old): return "Dispatchers cannot add or delete vehicles.", 403
    elif key == "sta":
        if not isinstance(val, list): return "Stations must be a list.", 400
        for s in val:
            m = E.check_station(s)
            if m: return m, 400
    elif key == "rou":
        for r in val:
            m = E.check_route(r)
            if m: return m, 400
    elif key in ("ses", "res"):
        sessions, reservations = (val, get("res")) if key == "ses" else (get("ses"), val)
        stations = {s["id"]: s for s in get("sta")}
        per = {}
        for x in sessions:
            if x["status"] == "Scheduled" and x["sid"] in stations:
                s = E.parse(x["start"]); per.setdefault(x["sid"], []).append((s, s + timedelta(minutes=x["mins"])))
        for x in reservations:
            if x["status"] == "Confirmed" and x["sid"] in stations:
                per.setdefault(x["sid"], []).append((E.parse(x["start"]), E.parse(x["end"])))
        for sid, iv in per.items():
            if E.max_concurrent(iv) > stations[sid]["n"]:
                return f"Station {sid} would be over its {stations[sid]['n']} connector(s) at that time. Choose another slot.", 409
        seen = []
        for x in reservations:
            if x["status"] != "Confirmed": continue
            a, b = E.parse(x["start"]), E.parse(x["end"])
            for y in seen:
                if y["sid"] == x["sid"] and y["cn"] == x["cn"] and E.overlap(a, b, E.parse(y["start"]), E.parse(y["end"])):
                    return "This charging slot conflicts with an existing reservation. Please select another slot.", 409
            seen.append(x)
    elif key == "pas":
        if who == DP:
            for vid, p in val.items():
                b = old.get(vid)
                if b is None or p["bal"] > b["bal"] or p["bal"] < 0 or p["status"] != b["status"]:
                    return "Dispatchers can only deduct charging costs from a pass.", 403
    elif key == "own":
        c = val.get("car", {})
        m = E.check_vehicle({**c, "name": c.get("name", "")})
        if m: return m, 400
    return None, 200


# ---------- routes ----------
@app.route("/api/health")
def health():
    return jsonify({"app": "urbanroute", "ok": True, "simulated_estimates": True})


@app.route("/api/state")
def get_state():
    return jsonify(state())


@app.route("/api/state/<key>", methods=["PUT"])
def put_state(key):
    if key not in KEYS: return err("Unknown collection.", 404)
    if role() not in (FM, DP, OW): return err("Send your role in the X-Role header.", 401)
    if role() not in WRITERS[key]: return err(f"{role()} cannot change {key}.", 403)
    val = request.get_json(silent=True)
    if val is None: return err("Body must be JSON.")
    msg, code = validate(key, val, role())
    if msg: return err(msg, code)
    put(key, val)
    return jsonify({"ok": True})


@app.route("/api/reset", methods=["POST"])
def reset():
    if role() != FM: return err("Only a fleet manager can reload sample data.", 403)
    seed_all()
    return jsonify({"ok": True})


@app.route("/api/route/check", methods=["POST"])
def route_check():
    b = request.get_json(silent=True) or {}
    v = next((x for x in get("veh") if x["id"] == b.get("vehicle_id")), None)
    stops = b.get("stops")
    if not v: return err("Unknown vehicle.", 404)
    m = E.check_route({"stops": stops})
    if m: return err(m)
    res = E.calc_route(stops, v)
    if not res["ok"]:
        best = (E.rank_stations(v, get("sta"), 60) or [None])[0]
        if best:
            res["suggested_stop"] = {"station": best["station"], "distance_km": best["distance_km"],
                                     "minutes": math.ceil(res["short_kwh"] / best["station"]["kw"] * 60),
                                     "estimate": best["estimate"]}
    return jsonify(res)


@app.route("/api/charging/estimate", methods=["POST"])
def charging_estimate():
    b = request.get_json(silent=True) or {}
    v = next((x for x in get("veh") if x["id"] == b.get("vehicle_id")), None)
    s = next((x for x in get("sta") if x["id"] == b.get("station_id")), None)
    if not v or not s: return err("Unknown vehicle or station.", 404)
    if s["conn"] != v["conn"]: return err("This station's connector does not fit the vehicle.")
    target = b.get("target")
    if not (E._num(target) and v["pct"] < target <= 100): return err("Target must be above the current charge and at most 100%.")
    try: start = E.parse(b["start"])
    except Exception: return err("Start time is required (ISO format).")
    mins = E.charge_minutes(v, s, v["pct"], target)
    length = timedelta(minutes=mins)
    busy = E.load(s["id"], start, start + length, get("ses"), get("res"))
    nxt = None if busy < s["n"] else E.next_free(s, start, length, get("ses"), get("res"))
    return jsonify({"energy_kwh": (target - v["pct"]) / 100 * v["kwh"], "minutes": mins,
                    "cost": (target - v["pct"]) / 100 * v["kwh"] * s["price"], "conflict": busy >= s["n"],
                    "next_free_start": E.iso(nxt) if nxt else None})


@app.route("/api/stations/discover")
def discover():
    v = next((x for x in get("veh") if x["id"] == request.args.get("vehicle_id")), None)
    if not v: return err("Unknown vehicle.", 404)
    try: radius = float(request.args.get("radius", 15))
    except ValueError: return err("Radius must be a number.")
    return jsonify(E.rank_stations(v, get("sta"), radius))


@app.route("/api/coordination")
def coordination():
    veh, rou = get("veh"), get("rou")
    urgent = {r["vid"] for r in rou if r["status"] == "Planned"}
    need = [{**v, "urgent": v["id"] in urgent} for v in veh if v["pct"] < 40 and v["status"] not in ("Offline", "Charging")]
    return jsonify(E.coordinate(need, get("sta")))


@app.route("/api/briefing")
def briefing():
    return jsonify(E.briefing(state()))


@app.route("/")
def index():
    return send_from_directory(FRONTEND, "index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
