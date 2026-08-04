from dataclasses import replace

import yaml
from fastapi.testclient import TestClient

import api.app as api_app


def test_calculate_exposes_canonical_result_schema(api_client: TestClient) -> None:
    api_app._ensure_initialized()
    fertilizer_name = next(iter(api_app.FERTILIZERS))
    payload = {
        "liters": 10,
        "fertilizers": [{"name": fertilizer_name, "grams": 1.5}],
        "urea_as_nh4": False,
        "water_mg_l": {"Ca": 5},
        "osmosis_percent": 10,
    }

    response = api_client.post("/calculate", json=payload)

    expected = api_app.compute_solution(
        {
            "liters": payload["liters"],
            "fertilizers": payload["fertilizers"],
            "urea_as_nh4": payload["urea_as_nh4"],
        },
        api_app.FERTILIZERS,
        api_app.MOLAR_MASSES,
        water_mg_l=dict(payload["water_mg_l"]),
        osmosis_percent=payload["osmosis_percent"],
    ).to_dict()

    assert response.status_code == 200
    assert response.json() == expected


def test_invalid_water_key_in_payload_returns_400(api_client: TestClient) -> None:
    response = api_client.post(
        "/calculate",
        json={
            "liters": 10,
            "fertilizers": [],
            "water_mg_l": {"INVALID": 1},
            "osmosis_percent": 0,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid water key: INVALID"


def test_invalid_water_key_in_profile_returns_400(api_client: TestClient, monkeypatch, tmp_path) -> None:
    layout = replace(api_app._portable_layout(), water_profiles=tmp_path)
    monkeypatch.setattr(api_app, "PORTABLE_LAYOUT", layout)
    profile_path = tmp_path / "broken.yml"
    profile_path.write_text(
        yaml.safe_dump(
            {
                "name": "broken",
                "mg_per_l": {"INVALID": 1},
                "osmosis_percent": 0,
            }
        ),
        encoding="utf-8",
    )

    response = api_client.post(
        "/calculate",
        json={
            "liters": 10,
            "fertilizers": [],
            "water_profile_name": "broken.yml",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid water key: INVALID"


def test_water_profile_name_without_suffix_is_accepted(api_client: TestClient, monkeypatch, tmp_path) -> None:
    layout = replace(api_app._portable_layout(), water_profiles=tmp_path)
    monkeypatch.setattr(api_app, "PORTABLE_LAYOUT", layout)
    profile_path = tmp_path / "simple.yml"
    profile_path.write_text(
        yaml.safe_dump(
            {
                "name": "simple",
                "mg_per_l": {"Ca": 5},
                "osmosis_percent": 0,
            }
        ),
        encoding="utf-8",
    )

    response = api_client.post(
        "/calculate",
        json={
            "liters": 10,
            "fertilizers": [],
            "water_profile_name": "simple",
        },
    )

    assert response.status_code == 200


def test_invalid_target_key_returns_400(api_client: TestClient) -> None:
    response = api_client.post(
        "/solve",
        json={
            "liters": 10,
            "targets": {"INVALID": 1},
            "fertilizers_allowed": [],
            "fixed_grams": {},
            "urea_as_nh4": False,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid target key: INVALID"


def test_solver_config_primitives_are_accepted(api_client: TestClient) -> None:
    response = api_client.post(
        "/solve",
        json={
            "liters": 10,
            "targets": {"N_total": 20},
            "fertilizers_allowed": ["Compo Basfoliar Top-N SL"],
            "fixed_grams": {},
            "urea_as_nh4": False,
            "solver_config": {
                "solver_model": "mass_nnls",
                "ignored_elements": ["Cu", "B"],
                "relative_weighting": True,
                "overshoot_penalty": 1.5,
                "n_total_governor_enabled": True,
                "n_total_governor_weight": 0.05,
            },
        },
    )

    assert response.status_code == 200
    assert response.json()["liters"] == 10
    assert response.json()["solver_model"] == "mass_nnls"
    assert response.json()["ignored_elements"] == ["Cu", "B"]


def test_invalid_solver_config_returns_400(api_client: TestClient) -> None:
    base_payload = {
        "liters": 10,
        "targets": {"N_total": 20},
        "fertilizers_allowed": ["Compo Basfoliar Top-N SL"],
    }
    cases = (
        ({"mystery": True}, "Unknown solver config key: mystery"),
        ({"relative_weighting": "false"}, "Invalid solver config value: relative_weighting"),
        ({"irls_max_outer_iter": 1.5}, "Invalid solver config value: irls_max_outer_iter"),
        ({"solver_model": "unknown"}, "Invalid solver config value: solver_model"),
        ({"ignored_elements": ["UNKNOWN"]}, "Invalid solver config value: ignored_elements"),
        (
            {"nitrogen_objective_mode": "chaos_mode"},
            "Invalid solver config value: nitrogen_objective_mode",
        ),
    )

    for solver_config, detail in cases:
        response = api_client.post(
            "/solve",
            json={**base_payload, "solver_config": solver_config},
        )
        assert response.status_code == 400
        assert response.json()["detail"] == detail


def test_hierarchical_solver_returns_resolved_priorities_and_stage_diagnostics(api_client: TestClient) -> None:
    response = api_client.post(
        "/solve",
        json={
            "liters": 10,
            "targets": {"N_total": 20},
            "fertilizers_allowed": ["Compo Basfoliar Top-N SL"],
            "solver_config": {
                "solver_model": "hierarchical",
                "target_priorities": {"N_total": {"under": 1, "over": 2}},
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["solver_model"] == "hierarchical"
    assert payload["target_priorities"] == {"N_total": {"under": 1, "over": 2}}
    assert [stage["priority"] for stage in payload["priority_stages"]] == [1, 2]
