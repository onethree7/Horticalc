from fastapi.testclient import TestClient

from api.app import app
from tests.frontend_assets import frontend_app_sources, frontend_module_entry


def test_frontend_root_serves_single_module_entry() -> None:
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "Horticalc GUI" in response.text
    assert response.text.count('type="module"') == 1
    assert frontend_module_entry() == "app/main.js"
    assert "app/state.js" not in response.text
    assert "app/app.js" not in response.text


def test_frontend_serves_every_es_module() -> None:
    client = TestClient(app)
    sources = frontend_app_sources()
    assert "app/main.js" in sources
    assert "app/storage.js" in sources
    assert "app/profiles.js" in sources
    for source in [*sources, "request_gate.js", "i18n/runtime.js"]:
        response = client.get(f"/{source}")
        assert response.status_code == 200, source
        assert response.text.strip(), source


def test_health_endpoint_still_available() -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
