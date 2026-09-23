import requests


BASE_URL = "http://127.0.0.1:8000"


def test_events():
    response = requests.get(
        f"{BASE_URL}/api/events",
        params={
            "equipment_id": "CRANE-001",
            "limit": 50,
        },
        timeout=5,
    )

    assert response.status_code == 200

    data = response.json()

    assert "count" in data
    assert "events" in data

    assert isinstance(data["count"], int)
    assert isinstance(data["events"], list)

    for event in data["events"]:
        assert "id" in event
        assert "equipment_id" in event
        assert "event_type" in event
        assert "event_time" in event
        assert "severity" in event
        assert "source" in event
        assert "message" in event

        assert event["equipment_id"] == "CRANE-001"


def test_critical_events():
    response = requests.get(
        f"{BASE_URL}/api/events",
        params={
            "equipment_id": "CRANE-001",
            "severity": "CRITICAL",
            "limit": 50,
        },
        timeout=5,
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data["events"], list)

    for event in data["events"]:
        assert event["equipment_id"] == "CRANE-001"
        assert event["severity"] == "CRITICAL"