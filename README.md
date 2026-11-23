# UrbanRoute Fleet

### Intelligent Electric Mobility Operations Platform

**PST Level 3 OJT | Track ID: PST_PD_165**

UrbanRoute Fleet is an electric vehicle fleet operations platform designed to improve fleet visibility, energy awareness, charging coordination, route planning and operational resilience.

The platform aims to bring vehicle readiness, charging infrastructure information and fleet coordination into one unified system.

## 1. Problem Statement

EV fleet operators often depend on multiple disconnected platforms to manage vehicles, locate charging stations and plan delivery routes.

This makes it difficult to monitor vehicle readiness, estimate charging delays and coordinate multiple vehicles efficiently.

UrbanRoute Fleet aims to address these challenges through a unified fleet management solution.

## 2. Core Modules

1. Vehicle Intelligence
2. Charging Infrastructure Management
3. Fleet Assignment Management
4. Energy Consumption Calculator
5. Driving Range Estimator
6. UrbanRoute Fleet Resilience OS
7. Disruption Recovery Simulation

## 3. Planned Features

- **Fleet Management:** Add, update and manage electric vehicles.
- **Charging Station Discovery:** Find nearby charging stations.
- **Connector Availability:** View available charging connectors.
- **Waiting Time Estimation:** Estimate waiting times at charging stations.
- **Charger Reliability:** Display estimated charger working probability.
- **Arrival Availability:** Estimate connector availability when a vehicle arrives.
- **Smart Route Planning:** Plan delivery routes based on vehicle battery range.
- **Charging Recommendations:** Suggest primary and backup charging stations.
- **Charging Reservations:** Simulate booking, cancellation and rescheduling.
- **Fleet Coordination:** Support coordinated charging for multiple vehicles.
- **UrbanRoute FleetPass:** A FASTag-inspired concept for simplified charging authorization and payment tracking.

## 4. Technology Stack

- Python
- Flask
- Flask-CORS
- SQLite
- HTML
- CSS
- JavaScript
- Git and GitHub

## 5. Project Structure

```text
URBANROUTE FLEET/
├── app/
│   ├── models/
│   ├── routes/
│   ├── services/
│   ├── static/
│   └── templates/
├── data/
├── docs/
├── instance/
├── tests/
├── config.py
├── requirements.txt
└── run.py
```

## 6. Installation and Setup

Clone the repository:

```bash
git clone https://github.com/aryathaokar22/Urbanroute-fleet-.git
```

Navigate into the project:

```bash
cd "URBANROUTE FLEET"
```

Create a virtual environment:

```bash
python3 -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the application:

```bash
python3 run.py
```

Open the application in your browser:

http://127.0.0.1:5000

## 7. Project Documentation

The Product Requirements Document (PRD) describes the project scope, user stories, functional requirements, system design and development milestones.

Refer to `UrbanRoute_Fleet_PRD_v0.2.docx` in the original project repository for detailed requirements.

Additional technical documentation is available in the `docs/` directory.

## 8. Team Members

- Arya Vijaykumar Thaokar
- Safa Shaikh

## 9. Development Status

**Phase:** Active Development

The project has moved from requirements and planning into software implementation.

The current application includes fleet management interfaces, energy and range calculations, and a demonstration of disruption recovery logic.

Advanced charging predictions, reservations, and FleetPass functionality are planned or simulated for demonstration purposes.

## 10. Project Goal

To develop a unified EV fleet charging and route planning solution that helps fleet operators make better operational decisions, improve vehicle utilization and manage charging more efficiently.

## Important Note

This project currently uses demonstration data and simulated operational recovery logic. It does not represent a live fleet management deployment.