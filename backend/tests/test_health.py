import requests


BASE_URL = "http://127.0.0.1:8000"


def test_fleet_health():
    response = requests.get(
        f"{BASE_URL}/api/health/fleet",
        timeout=5,
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 1

    for equipment in data:
        assert "equipment_id" in equipment
        assert "health_score" in equipment
        assert "status" in equipment

        assert isinstance(equipment["health_score"], (int, float))
        assert 0 <= equipment["health_score"] <= 100

        assert equipment["status"] in {
            "NORMAL",
            "WARNING",
            "CRITICAL",
        }