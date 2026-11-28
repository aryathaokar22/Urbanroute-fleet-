# UrbanRoute Fleet

EV fleet charging and route planning demo with three dashboards: **Fleet manager**, **Dispatcher** and **EV owner**.

- `frontend/index.html`: the whole UI (HTML, CSS, vanilla JavaScript, no build step)
- `backend/`: Python Flask API with SQLite storage and the range, charging and coordination engine

## Run it

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open http://localhost:5000. The server also serves the front end, and the app shows a **Server connected** badge. Data is shared across browsers and survives clearing browser storage.

**Without the backend:** open `frontend/index.html` directly or host it on GitHub Pages. It falls back to browser `localStorage` and shows **Saved in this browser**.

**Frontend on GitHub Pages, backend elsewhere:** open the page with `?api=https://your-backend-url`. The address is remembered in `localStorage` under `urbanroute_api`.

## Tests

```bash
cd backend && python -m unittest -v
```

19 tests cover hand-calculated range, energy, charging time and shortfall cases, capacity checks, fleet coordination, validation messages and role rules.

## API

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | Server check |
| GET | `/api/state` | All saved data |
| PUT | `/api/state/<key>` | Save a collection (`veh, sta, ses, rou, res, pas, txn, own`). Validated and role-checked |
| POST | `/api/route/check` | Distance, energy, arrival battery and charging stop for a route |
| POST | `/api/charging/estimate` | Energy, time, cost and slot conflict for a charging session |
| GET | `/api/stations/discover?vehicle_id=&radius=` | Compatible stations ranked, with primary and backup |
| GET | `/api/coordination` | Fleet charging plan within connector capacity |
| GET | `/api/briefing` | Rule-based fleet briefing |
| POST | `/api/reset` | Reload sample data (fleet manager only) |

Errors use clear messages: `400` invalid input, `403` role not allowed, `409` slot conflict.

## Roles

Send the role in the `X-Role` header (`Fleet Manager`, `Dispatcher`, `EV Owner`).

- Fleet manager: all fleet data
- Dispatcher: routes, sessions, reservations; may change vehicle **status** only; cannot edit stations
- EV owner: own car and charging log only

This enforces permissions for the demo but is **not authentication**. There are no accounts or passwords, so anyone can set the header.

## Model and assumptions

- Range = battery kWh x charge % / consumption
- Route energy = total km x consumption; a route passes if arrival battery is at least 10%
- Charging time = energy / station kW x 60 (rounded up)
- Constant consumption and charging power. No traffic, weather or charge taper
- Station free connectors, waiting time, reliability, arrival availability and FleetPass balances are **simulated**
- The "AI" briefing is fixed rules over saved data, not a machine learning model

## Limits

Saves are last-write-wins per collection. No live GPS, charger network or payments. SQLite on free hosts may reset when the service restarts.
