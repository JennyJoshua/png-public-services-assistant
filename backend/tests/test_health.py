from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_expected_status() -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "png-public-services-assistant-api",
        "version": "0.2.0",
    }


def test_health_does_not_expose_environment_details() -> None:
    response = client.get("/api/v1/health")
    body = response.text.lower()

    assert "secret" not in body
    assert "password" not in body
    assert "environment" not in body
