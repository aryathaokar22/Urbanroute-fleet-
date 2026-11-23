
# UrbanRoute Fleet — API Documentation

Base URL:

`http://127.0.0.1:5000`

## 1. Energy Calculator

**Endpoint:** `/api/energy`

**Method:** POST

**Purpose:** Calculates the energy required for a journey.

Example request:

```json
{
  "distance": 100,
  "consumption": 15
}
```

Example response:

```json
{
  "distance_km": 100,
  "energy_required_kwh": 15
}
```

Formula:

`Energy = Distance × Consumption / 100`

## 2. Driving Range Estimator

**Endpoint:** `/api/range`

**Method:** POST

**Purpose:** Estimates the vehicle's driving range based on available battery energy.

Example request:

```json
{
  "battery": 60,
  "level": 50,
  "consumption": 15
}
```

Example response:

```json
{
  "estimated_range_km": 200
}
```

Formula:

`Range = Available Battery Energy / Consumption × 100`

## 3. Disruption Simulation

**Endpoint:** `/api/disruption`

**Method:** POST

**Purpose:** Simulates a vehicle disruption and searches for an eligible replacement vehicle.

Example request:

```json
{
  "type": "Vehicle Breakdown",
  "target": "UR-001"
}
```

The response identifies a recovery candidate using the current demonstration rules, or reports that no feasible candidate was found.

## 4. Error Responses

The API may return:

- `400` — Invalid input
- `200` — Request processed successfully

## Important

These endpoints currently use simplified demonstration logic. They are not connected to live fleet systems.
