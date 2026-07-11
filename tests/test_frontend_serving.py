from fastapi.testclient import TestClient

from api.app import app
from tests.frontend_assets import frontend_app_sources

EXPECTED_APP_SOURCES = [
    "app/dom.js",
    "app/state.js",
    "app/units.js",
    "app/notifications.js",
    "app/shell.js",
    "app/api.js",
    "app/calculator.js",
    "app/water.js",
    "app/solver.js",
    "app/editor.js",
    "app/i18n-controls.js",
    "app/app.js",
]


def test_frontend_root_serves_index() -> None:
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "Horticalc GUI" in response.text
    assert "request_gate.js" in response.text

    request_gate = client.get("/request_gate.js")
    assert request_gate.status_code == 200
    assert "createLatestRequestGate" in request_gate.text


def test_frontend_serves_complete_modular_app_in_dependency_order() -> None:
    client = TestClient(app)
    sources = frontend_app_sources()

    assert sources == EXPECTED_APP_SOURCES
    assert client.get("/app.js").status_code == 404
    for source in sources:
        response = client.get(f"/{source}")
        assert response.status_code == 200, source
        assert response.text.strip(), source


def test_health_endpoint_still_available() -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
