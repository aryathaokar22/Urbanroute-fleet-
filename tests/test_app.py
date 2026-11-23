
import pytest
from app import create_app


@pytest.fixture
def client(tmp_path):
    test_database = tmp_path / "test_urbanroute.db"

    app = create_app({
        "TESTING": True,
        "DATABASE": str(test_database)
    })

    with app.test_client() as client:
        yield client


def test_home_page(client):
    assert client.get("/").status_code == 200


def test_dashboard_page(client):
    assert client.get("/dashboard").status_code == 200


def test_vehicles_page(client):
    assert client.get("/dashboard/vehicles").status_code == 200


def test_chargers_page(client):
    assert client.get("/dashboard/chargers").status_code == 200


def test_assignments_page(client):
    assert client.get("/dashboard/assignments").status_code == 200


def test_energy_calculation(client):
    response = client.post(
        "/api/energy",
        json={"distance": 100, "consumption": 15}
    )

    assert response.status_code == 200
    assert response.json["energy_required_kwh"] == 15


def test_range_calculation(client):
    response = client.post(
        "/api/range",
        json={"battery": 60, "level": 50, "consumption": 15}
    )

    assert response.status_code == 200
    assert response.json["estimated_range_km"] == 200


def test_invalid_energy_input(client):
    response = client.post(
        "/api/energy",
        json={"distance": -100, "consumption": 15}
    )

    assert response.status_code == 400
