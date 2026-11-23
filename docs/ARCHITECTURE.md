
# UrbanRoute Fleet — System Architecture

## 1. Overview

UrbanRoute Fleet is an electric vehicle fleet operations platform designed to support fleet visibility, energy awareness, charging coordination and operational recovery.

## 2. Technology Stack

| Layer | Technology |
|---|---|
| Backend | Python |
| Web Framework | Flask |
| Database | SQLite |
| Frontend | HTML |
| Styling | CSS |
| Client-side Logic | JavaScript |
| Testing | Pytest |

## 3. Application Structure

- `app/` — Main application package
- `app/routes/` — Web pages and API endpoints
- `app/models/` — Database model package
- `app/services/` — Business logic services
- `app/templates/` — HTML templates
- `app/static/` — CSS, JavaScript and images
- `data/` — Dataset documentation
- `docs/` — Project documentation
- `instance/` — Local database and seed data
- `tests/` — Automated tests

## 4. Core Modules

1. Fleet Dashboard
2. Vehicle Management
3. Charging Infrastructure
4. Assignment Management
5. Energy Consumption Calculator
6. Driving Range Estimator
7. Disruption Simulation
8. UrbanRoute Fleet Resilience OS

## 5. Data Flow

1. Users interact with the frontend.
2. JavaScript sends requests to Flask API endpoints.
3. Flask processes requests and applies business rules.
4. SQLite stores and retrieves operational records.
5. Flask returns responses to the frontend.

## 6. Innovation Direction

The long-term innovation is UrbanRoute Fleet Resilience OS.

Its goal is to identify operational disruptions and generate recovery plans that preserve as many delivery commitments as possible while respecting vehicle, battery and operational constraints.

## 7. Current Limitations

- Demonstration dataset only
- No live vehicle telemetry
- No live charging station integration
- Disruption recovery uses simplified demonstration rules
- No production deployment yet
