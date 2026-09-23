import requests


BASE_URL = "http://127.0.0.1:8000"


def test_system_health():
    response = requests.get(
        f"{BASE_URL}/api/system/health",
        timeout=5,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert data["mqtt"] == "configured"
    assert "timestamp" in data