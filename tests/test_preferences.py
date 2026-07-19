from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import api.app as api_app
from horticalc import paths
from horticalc.data_io import load_user_preferences, save_user_preferences


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


def test_volume_unit_preference_persists_and_rejects_ambiguous_unit(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(paths, "app_root", lambda: tmp_path)
    client = TestClient(api_app.app)

    response = client.put("/preferences", json={"volume_unit": "us_gallon"})

    assert response.status_code == 200
    assert response.json()["volume_unit"] == "us_gallon"
    rejected = client.put("/preferences", json={"volume_unit": "gallon"})
    assert rejected.status_code == 400
    assert rejected.json()["detail"] == "Unknown volume unit"


def test_dose_unit_preferences_persist_and_validate_dimension(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(paths, "app_root", lambda: tmp_path)
    client = TestClient(api_app.app)

    response = client.put(
        "/preferences",
        json={"solid_dose_unit": "ounce", "liquid_dose_unit": "us_fluid_ounce"},
    )

    assert response.status_code == 200
    assert response.json()["solid_dose_unit"] == "ounce"
    assert response.json()["liquid_dose_unit"] == "us_fluid_ounce"
    assert client.put("/preferences", json={"solid_dose_unit": "milliliter"}).status_code == 400
    assert client.put("/preferences", json={"liquid_dose_unit": "gram"}).status_code == 400


def test_preferences_merge_typed_workspace_defaults(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(paths, "app_root", lambda: tmp_path)
    client = TestClient(api_app.app)
    assert client.put("/preferences", json={"theme": "soil"}).status_code == 200

    response = client.put(
        "/preferences",
        json={
            "locale": "es",
            "default_liters": 100,
            "last_water_profile": "tap.yml",
            "solver_config": {
                "solver_model": "hierarchical",
                "relative_weighting": True,
                "overshoot_penalty": 1.2,
                "target_priorities": {
                    "N_total": {"under": 1, "over": 1},
                    "Ca": {"under": 2, "over": 3},
                },
            },
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "theme": "soil",
        "locale": "es",
        "default_liters": 100.0,
        "last_water_profile": "tap.yml",
        "solver_config": {
            "solver_model": "hierarchical",
            "relative_weighting": True,
            "overshoot_penalty": 1.2,
            "target_priorities": {
                "N_total": {"under": 1, "over": 1},
                "Ca": {"under": 2, "over": 3},
            },
        },
    }
    assert client.get("/preferences").json() == response.json()


def test_locale_preference_rejects_unknown_locale(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(paths, "app_root", lambda: tmp_path)

    response = TestClient(api_app.app).put("/preferences", json={"locale": "fr"})

    assert response.status_code == 400
    assert response.json()["detail"] == "Unknown locale"


def test_preferences_reject_unknown_solver_key_and_profile_path(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(paths, "app_root", lambda: tmp_path)
    client = TestClient(api_app.app)

    assert client.put("/preferences", json={"solver_config": {"mystery": True}}).status_code == 400
    assert client.put("/preferences", json={"last_water_profile": "../tap.yml"}).status_code == 400


def test_preferences_reject_advanced_solver_config(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(paths, "app_root", lambda: tmp_path)
    client = TestClient(api_app.app)

    advanced = client.put(
        "/preferences",
        json={"solver_config": {"n_form_priority_weights": {"N_NO3": 3.0}}},
    )
    rejected = client.put(
        "/preferences",
        json={"solver_config": {"relative_weighting": "false"}},
    )

    assert advanced.status_code == 400
    assert advanced.json()["detail"] == ("Advanced solver config key is not accepted here: n_form_priority_weights")
    assert rejected.status_code == 400
    assert rejected.json()["detail"] == "Invalid solver config value: relative_weighting"


def test_preferences_can_reset_solver_config_to_defaults(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(paths, "app_root", lambda: tmp_path)
    client = TestClient(api_app.app)
    assert (
        client.put(
            "/preferences",
            json={"solver_config": {"relative_weighting": True}},
        ).status_code
        == 200
    )

    response = client.put("/preferences", json={"solver_config": {}})

    assert response.status_code == 200
    assert response.json()["solver_config"] == {}
    assert client.get("/preferences").json()["solver_config"] == {}


@pytest.mark.parametrize("content", ["{broken", "[]", '{"value": NaN}'])
def test_invalid_preferences_are_logged_and_ignored(
    monkeypatch,
    tmp_path,
    caplog,
    content: str,
) -> None:
    monkeypatch.setattr(paths, "app_root", lambda: tmp_path)
    preference_path = paths.user_preferences_path(tmp_path)
    preference_path.parent.mkdir(parents=True)
    preference_path.write_text(content, encoding="utf-8")

    assert load_user_preferences() == {}
    assert "Ignoring invalid preferences file" in caplog.text


def test_preferences_save_rejects_non_finite_numbers(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(paths, "app_root", lambda: tmp_path)

    with pytest.raises(ValueError, match="finite numbers"):
        save_user_preferences({"default_liters": float("inf")})

    assert not paths.user_preferences_path(tmp_path).exists()


def test_preferences_save_requires_object(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(paths, "app_root", lambda: tmp_path)

    with pytest.raises(ValueError, match="JSON object"):
        save_user_preferences(["invalid"])

    assert not paths.user_preferences_path(tmp_path).exists()
