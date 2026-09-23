import requests


BASE_URL = "http://127.0.0.1:8000"


def test_latest_telemetry():
    response = requests.get(
        f"{BASE_URL}/api/telemetry/latest",
        timeout=5,
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 1

    telemetry = data[0]

    required_fields = {
        "equipment_id",
        "timestamp",
        "temperature",
        "vibration",
        "load_percentage",
        "motor_current",
        "rpm",
        "operating_hours",
    }

    assert required_fields.issubset(telemetry.keys())


def test_telemetry_history():
    response = requests.get(
        f"{BASE_URL}/api/telemetry/history",
        params={
            "equipment_id": "CRANE-001",
            "minutes": 10,
        },
        timeout=5,
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)

    if data:
        assert data[0]["equipment_id"] == "CRANE-001"