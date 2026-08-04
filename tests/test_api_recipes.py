from fastapi.testclient import TestClient

import api.app as api_app
from horticalc.solver_config import SOLVER_CONFIG_DEFINITIONS


def test_yaml_filename_normalizes_route_input() -> None:
    assert api_app._yaml_filename("../secret.yml") == "secret.yml"
    assert api_app._yaml_filename("My Recipe") == "My_Recipe.yml"


def test_recipes_filters_solver_and_default(api_client: TestClient) -> None:
    response = api_client.get("/recipes")

    assert response.status_code == 200

    filenames = {entry["filename"] for entry in response.json()}
    assert "default.yml" not in filenames
    assert not any(name.startswith("solve_") for name in filenames)
    assert "golden.yml" in filenames


def test_recipe_payload_persists_fertilizers_allowed(api_client: TestClient) -> None:
    payload = {
        "name": "api_recipe_allowed_roundtrip",
        "liters": 10,
        "fertilizers": [{"name": "Calcinit", "grams": 1.5}],
        "fertilizers_allowed": ["Calcinit", "Hakaphos Rot"],
        "urea_as_nh4": False,
    }

    save_response = api_client.post("/recipes", json=payload)
    assert save_response.status_code == 200

    get_response = api_client.get("/recipes/api_recipe_allowed_roundtrip")
    assert get_response.status_code == 200
    recipe = get_response.json()
    assert recipe.get("fertilizers_allowed") == ["Calcinit", "Hakaphos Rot"]


def test_recipe_payload_persists_solver_config(api_client: TestClient) -> None:
    payload = {
        "name": "api_recipe_solver_config_roundtrip",
        "liters": 30,
        "fertilizers": [{"name": "Calcinit", "grams": 4.5}],
        "solver_config": {
            "solver_model": "hierarchical",
            "target_priorities": {
                "N_total": {"under": 1, "over": 1},
                "Ca": {"under": 2, "over": 3},
            },
            "relative_weighting": True,
            "overshoot_penalty": 1.5,
            "n_total_governor_enabled": True,
            "n_total_governor_weight": 0.05,
            "n_form_priority_weights": {"N_NO3": 3.0},
        },
    }

    save_response = api_client.post("/recipes", json=payload)
    assert save_response.status_code == 200

    get_response = api_client.get("/recipes/api_recipe_solver_config_roundtrip")
    assert get_response.status_code == 200
    recipe = get_response.json()
    assert recipe.get("solver_config") == payload["solver_config"]


def test_solver_config_schema_matches_backend_definitions(api_client: TestClient) -> None:
    response = api_client.get("/schema/solver-config")

    assert response.status_code == 200
    assert response.json() == {"definitions": list(SOLVER_CONFIG_DEFINITIONS)}


def test_recipe_save_rejects_invalid_solver_config(api_client: TestClient) -> None:
    response = api_client.post(
        "/recipes",
        json={
            "name": "invalid_solver_config",
            "solver_config": {"relative_weighting": "false"},
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid solver config value: relative_weighting"


def test_recipe_save_rejects_duplicate_fertilizers_allowed(api_client: TestClient) -> None:
    response = api_client.post(
        "/recipes",
        json={
            "name": "invalid_duplicate_recipe",
            "fertilizers_allowed": ["Calcinit", "Calcinit"],
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "fertilizers_allowed must not contain duplicates: ['Calcinit']"
