from __future__ import annotations

from fastapi.testclient import TestClient

import api.app as api_app
from horticalc import paths


def test_theme_preference_persists_in_user_directory(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(paths, "app_root", lambda: tmp_path)
    client = TestClient(api_app.app)

    response = client.put("/preferences", json={"theme": "soil"})

    assert response.status_code == 200
    assert client.get("/preferences").json() == {"theme": "soil"}
    assert paths.user_preferences_path(tmp_path).exists()


def test_theme_preference_rejects_unknown_theme(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(paths, "app_root", lambda: tmp_path)
    response = TestClient(api_app.app).put("/preferences", json={"theme": "surprise-me"})

    assert response.status_code == 400


def test_preferences_merge_typed_workspace_defaults(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(paths, "app_root", lambda: tmp_path)
    client = TestClient(api_app.app)
    assert client.put("/preferences", json={"theme": "soil"}).status_code == 200

    response = client.put(
        "/preferences",
        json={
            "default_liters": 100,
            "last_water_profile": "tap.yml",
            "solver_config": {"relative_weighting": True, "overshoot_penalty": 1.2},
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "theme": "soil",
        "default_liters": 100.0,
        "last_water_profile": "tap.yml",
        "solver_config": {"relative_weighting": True, "overshoot_penalty": 1.2},
    }
    assert client.get("/preferences").json() == response.json()


def test_preferences_reject_unknown_solver_key_and_profile_path(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(paths, "app_root", lambda: tmp_path)
    client = TestClient(api_app.app)

    assert client.put("/preferences", json={"solver_config": {"mystery": True}}).status_code == 400
    assert client.put("/preferences", json={"last_water_profile": "../tap.yml"}).status_code == 400
