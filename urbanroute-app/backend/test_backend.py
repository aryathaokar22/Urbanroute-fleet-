"""Run: python -m unittest -v   (hand-calculated cases from the PRD evaluation)"""
import os, tempfile, unittest
from datetime import datetime, timezone

os.environ["URBANROUTE_DB"] = os.path.join(tempfile.mkdtemp(), "t.db")
import engine as E
from app import app

V101 = {"id": "UR-101", "kwh": 21.3, "cons": .14, "pct": 82, "conn": "CCS2"}
V102 = {"id": "UR-102", "kwh": 15, "cons": .13, "pct": 24, "conn": "CCS2"}


class Engine(unittest.TestCase):
    def test_range(self):
        # 21.3 x 0.82 = 17.466 kWh; / 0.14 = 124.76 km
        self.assertAlmostEqual(E.range_km(V101), 124.757, places=2)

    def test_route_can_finish(self):
        r = E.calc_route([{"n": "A", "km": 24}, {"n": "B", "km": 12}, {"n": "C", "km": 30}], V101)
        self.assertAlmostEqual(r["kwh"], 9.24, places=2)            # 66 km x 0.14
        self.assertAlmostEqual(r["arrival_pct"], 38.6, places=1)    # (17.466-9.24)/21.3
        self.assertTrue(r["ok"])

    def test_route_short(self):
        r = E.calc_route([{"n": "A", "km": 40}], V102)
        # avail 3.6, need 5.2, reserve 1.5 -> short 3.1 kWh
        self.assertFalse(r["ok"])
        self.assertAlmostEqual(r["short_kwh"], 3.1, places=2)

    def test_charge_minutes(self):
        st = {"kw": 50}
        # 21.3 kWh, 20% to 80% = 12.78 kWh / 50 kW = 15.34 min -> 16
        self.assertEqual(E.charge_minutes(V101, st, 20, 80), 16)

    def test_capacity_sweep(self):
        a = datetime(2026, 1, 1, 10, tzinfo=timezone.utc)
        h = lambda n: a.replace(hour=a.hour + n)
        self.assertEqual(E.max_concurrent([(h(0), h(1)), (h(1), h(2))]), 1)   # back to back
        self.assertEqual(E.max_concurrent([(h(0), h(2)), (h(1), h(3))]), 2)

    def test_coordination_respects_capacity(self):
        st = [{"id": "S", "conn": "CCS2", "n": 1, "lat": 0, "lng": 0}]
        vs = [{"id": f"V{i}", "pct": 10 + i, "conn": "CCS2", "lat": 0, "lng": 0} for i in range(3)]
        r = E.coordinate(vs, st, horizon=2)
        self.assertEqual(len(r["assignments"]), 2)
        self.assertEqual(len(r["unassigned"]), 1)
        self.assertEqual(r["assignments"][0]["vehicle"], "V0")  # lowest battery first

    def test_validation_messages(self):
        self.assertEqual(E.check_station({"name": "x", "kw": 0, "n": 1, "price": 1}), "Station power must be greater than 0 kW.")


class Api(unittest.TestCase):
    def setUp(self):
        self.c = app.test_client()
        self.c.post("/api/reset", headers={"X-Role": "Fleet Manager"})

    def put(self, key, val, role):
        return self.c.put(f"/api/state/{key}", json=val, headers={"X-Role": role})

    def test_health_and_state(self):
        self.assertTrue(self.c.get("/api/health").get_json()["ok"])
        s = self.c.get("/api/state").get_json()
        self.assertEqual(len(s["veh"]), 8)

    def test_no_role_blocked(self):
        self.assertEqual(self.c.put("/api/state/veh", json=[]).status_code, 401)

    def test_dispatcher_cannot_edit_vehicle_or_station(self):
        veh = self.c.get("/api/state").get_json()["veh"]
        veh[0]["name"] = "Hacked"
        self.assertEqual(self.put("veh", veh, "Dispatcher").status_code, 403)
        self.assertEqual(self.put("sta", [], "Dispatcher").status_code, 403)

    def test_dispatcher_can_change_status(self):
        veh = self.c.get("/api/state").get_json()["veh"]
        veh[0]["status"] = "Charging Scheduled"
        self.assertEqual(self.put("veh", veh, "Dispatcher").status_code, 200)

    def test_owner_cannot_touch_fleet(self):
        self.assertEqual(self.put("veh", [], "EV Owner").status_code, 403)

    def test_invalid_vehicle_rejected(self):
        veh = self.c.get("/api/state").get_json()["veh"]
        veh[0]["kwh"] = -5
        r = self.put("veh", veh, "Fleet Manager")
        self.assertEqual(r.status_code, 400)
        self.assertIn("Battery capacity", r.get_json()["error"])

    def test_station_power_validation(self):
        sta = self.c.get("/api/state").get_json()["sta"]
        sta[0]["kw"] = 0
        self.assertEqual(self.put("sta", sta, "Fleet Manager").status_code, 400)

    def test_reservation_conflict(self):
        res = self.c.get("/api/state").get_json()["res"]
        dup = dict(res[0], id="RS-2")
        # same station, connector 1 and time as RS-1 -> overlapping reservation
        r = self.put("res", res + [dup], "Dispatcher")
        self.assertEqual(r.status_code, 409)

    def test_route_check_endpoint(self):
        r = self.c.post("/api/route/check", json={"vehicle_id": "UR-102", "stops": [{"n": "A", "km": 40}]}).get_json()
        self.assertFalse(r["ok"])
        self.assertAlmostEqual(r["short_kwh"], 3.1, places=2)
        self.assertIn("suggested_stop", r)

    def test_charging_estimate_and_incompatible(self):
        ok = self.c.post("/api/charging/estimate", json={"vehicle_id": "UR-102", "station_id": "ST-1",
                         "start": "2030-01-01T10:00:00Z", "target": 80}).get_json()
        self.assertEqual(ok["minutes"], 11)  # 15 kWh x 56% = 8.4 kWh; / 50 kW = 10.08 min -> 11
        self.assertAlmostEqual(ok["energy_kwh"], 8.4, places=2)
        bad = self.c.post("/api/charging/estimate", json={"vehicle_id": "UR-102", "station_id": "ST-4",
                          "start": "2030-01-01T10:00:00Z", "target": 80})
        self.assertEqual(bad.status_code, 400)

    def test_discover_only_compatible(self):
        r = self.c.get("/api/stations/discover?vehicle_id=UR-104&radius=50").get_json()
        self.assertTrue(r and all(x["station"]["conn"] == "Type 2" for x in r))
        self.assertTrue(all(x["estimate"]["is_simulated"] for x in r))

    def test_briefing_and_coordination(self):
        self.assertIsInstance(self.c.get("/api/briefing").get_json(), list)
        self.assertIn("assignments", self.c.get("/api/coordination").get_json())


if __name__ == "__main__":
    unittest.main()
