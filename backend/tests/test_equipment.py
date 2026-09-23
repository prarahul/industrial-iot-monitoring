import requests


BASE_URL = "http://127.0.0.1:8000"


def test_equipment_list():
    response = requests.get(
        f"{BASE_URL}/api/equipment",
        timeout=5,
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 1

    equipment_ids = [
        equipment["equipment_id"]
        for equipment in data
    ]

    assert "CRANE-001" in equipment_ids
    assert "CRANE-002" in equipment_ids
    assert "CRANE-003" in equipment_ids