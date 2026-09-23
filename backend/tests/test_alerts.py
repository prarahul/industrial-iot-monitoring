import requests


BASE_URL = "http://127.0.0.1:8000"


def test_active_alerts():
    response = requests.get(
        f"{BASE_URL}/api/alerts",
        params={
            "equipment_id": "CRANE-001",
            "status": "ACTIVE",
            "limit": 50,
        },
        timeout=5,
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)

    for alert in data:
        assert "id" in alert
        assert "equipment_id" in alert
        assert "type" in alert
        assert "severity" in alert
        assert "message" in alert
        assert "status" in alert

        assert alert["equipment_id"] == "CRANE-001"
        assert alert["status"] == "ACTIVE"
        assert alert["severity"] in {
            "INFO",
            "WARNING",
            "CRITICAL",
        }


def test_alerts_for_equipment():
    response = requests.get(
        f"{BASE_URL}/api/alerts",
        params={
            "equipment_id": "CRANE-001",
            "limit": 50,
        },
        timeout=5,
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)

    for alert in data:
        assert alert["equipment_id"] == "CRANE-001"