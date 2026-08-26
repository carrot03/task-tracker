from datetime import datetime


def test_health_check_returns_200_with_status_and_timestamp(client):
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    # raises ValueError if not a valid ISO 8601 timestamp
    datetime.fromisoformat(body["timestamp"])
