from dataclasses import replace

import pytest
from fastapi.testclient import TestClient

import api.app as api_app


def test_yaml_save_rejects_malformed_or_non_object_payloads() -> None:
    client = TestClient(api_app.app, raise_server_exceptions=False)

    malformed = client.post(
        "/water-profiles",
        content="name: [",
        headers={"content-type": "application/yaml"},
    )
    non_object = client.post(
        "/water-profiles",
        content="- name: profile",
        headers={"content-type": "application/yaml"},
    )
    empty_list = client.post(
        "/water-profiles",
        content="[]",
        headers={"content-type": "application/yaml"},
    )

    assert malformed.status_code == 400
    assert malformed.json()["detail"] == "Invalid request payload"
    assert non_object.status_code == 400
    assert non_object.json()["detail"] == "Request payload must be an object"
    assert empty_list.status_code == 400
    assert empty_list.json()["detail"] == "Request payload must be an object"


def test_yaml_save_rejects_non_finite_target(monkeypatch, tmp_path) -> None:
    layout = api_app._portable_layout()
    monkeypatch.setattr(
        api_app,
        "PORTABLE_LAYOUT",
        replace(layout, nutrient_solutions=tmp_path),
    )

    response = TestClient(api_app.app).post(
        "/nutrient-solutions",
        content="name: invalid\ntargets_mg_per_l:\n  N_total: .nan\n",
        headers={"content-type": "application/yaml"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid value for N_total"
    assert not (tmp_path / "invalid.yml").exists()


def test_solve_rejects_unknown_water_key() -> None:
    response = TestClient(api_app.app).post(
        "/solve",
        json={
            "targets": {"N_total": 10},
            "fertilizers_allowed": ["Yara Tera CALCINIT"],
            "water_profile": {"mg_per_l": {"UNKNOWN": 1}},
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid water key: UNKNOWN"


def test_solve_rejects_duplicate_fertilizers_allowed() -> None:
    response = TestClient(api_app.app).post(
        "/solve",
        json={
            "targets": {"N_total": 10},
            "fertilizers_allowed": ["Yara Tera CALCINIT", "Yara Tera CALCINIT"],
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == ("fertilizers_allowed must not contain duplicates: ['Yara Tera CALCINIT']")


def test_requests_reject_non_finite_runtime_numbers() -> None:
    client = TestClient(api_app.app)
    requests = [
        ("/calculate", '{"liters": Infinity}'),
        (
            "/calculate",
            '{"fertilizers": [{"name": "Yara Tera CALCINIT", "grams": Infinity}]}',
        ),
        ("/calculate", '{"osmosis_percent": Infinity}'),
        ("/solve", '{"fixed_grams": {"Yara Tera CALCINIT": Infinity}}'),
        (
            "/nutrient-solutions",
            '{"name": "bad", "fixed_grams": {"Yara Tera CALCINIT": Infinity}}',
        ),
    ]

    for route, payload in requests:
        response = client.post(route, content=payload, headers={"content-type": "application/json"})
        assert response.status_code == 422, (route, response.text)


@pytest.mark.parametrize(
    ("payload", "expected_status"),
    [
        ({"name": "bad liters", "liters": 0}, 422),
        ({"name": "bad osmosis", "osmosis_percent": 101}, 422),
        (
            {
                "name": "bad fixed amount",
                "fertilizers_allowed": ["A"],
                "fixed_grams": {"A": -1},
            },
            400,
        ),
    ],
)
def test_nutrient_solution_rejects_invalid_solver_setup_numbers(
    payload: dict,
    expected_status: int,
) -> None:
    response = TestClient(api_app.app).post("/nutrient-solutions", json=payload)

    assert response.status_code == expected_status


@pytest.mark.parametrize(
    "payload",
    [
        {"liters": 0},
        {"fertilizers": [{"name": "Yara Tera CALCINIT", "grams": -1}]},
        {"osmosis_percent": -1},
        {"osmosis_percent": 101},
    ],
)
def test_calculate_model_bounds_return_422(payload: dict) -> None:
    assert TestClient(api_app.app).post("/calculate", json=payload).status_code == 422


def test_calculate_mapping_domain_violation_returns_400() -> None:
    response = TestClient(api_app.app).post("/calculate", json={"water_mg_l": {"Ca": -1}})
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid value for Ca"


def test_solve_rejects_non_finite_nested_water_osmosis() -> None:
    response = TestClient(api_app.app).post(
        "/solve",
        content='{"water_profile": {"mg_per_l": {}, "osmosis_percent": Infinity}}',
        headers={"content-type": "application/json"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid osmosis_percent value"


@pytest.mark.parametrize("mg_per_l", [[], ""])
def test_solve_rejects_non_object_nested_water_values(mg_per_l) -> None:
    response = TestClient(api_app.app).post(
        "/solve",
        json={"water_profile": {"mg_per_l": mg_per_l}},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "water_profile.mg_per_l must be an object"


def test_resource_list_skips_invalid_yaml(monkeypatch, tmp_path, caplog) -> None:
    layout = api_app._portable_layout()
    user_recipes = tmp_path / "user" / "recipes"
    user_recipes.mkdir(parents=True)
    monkeypatch.setattr(
        api_app,
        "PORTABLE_LAYOUT",
        replace(layout, root=tmp_path, recipes=user_recipes),
    )
    (user_recipes / "good.yml").write_text("name: Good\nliters: 10\n", encoding="utf-8")
    (user_recipes / "broken.yml").write_text("name: [", encoding="utf-8")

    response = TestClient(api_app.app).get("/recipes")

    assert response.status_code == 200
    assert response.json() == [{"name": "Good", "filename": "good.yml"}]
    assert "Skipping invalid YAML resource" in caplog.text
