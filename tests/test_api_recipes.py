import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from api.app import app


def test_recipes_filters_solver_and_default() -> None:
    client = TestClient(app)
    response = client.get("/recipes")

    assert response.status_code == 200

    filenames = {entry["filename"] for entry in response.json()}
    assert "default.yml" not in filenames
    assert not any(name.startswith("solve_") for name in filenames)
    assert "golden.yml" in filenames
