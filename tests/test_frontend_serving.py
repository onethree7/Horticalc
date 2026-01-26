from fastapi.testclient import TestClient

from api.app import app


def test_frontend_root_serves_index() -> None:
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "Horticalc GUI" in response.text


def test_health_endpoint_still_available() -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
