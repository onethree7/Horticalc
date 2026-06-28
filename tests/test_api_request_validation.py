from dataclasses import replace

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

    assert malformed.status_code == 400
    assert malformed.json()["detail"] == "Invalid request payload"
    assert non_object.status_code == 400
    assert non_object.json()["detail"] == "Request payload must be an object"


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
    ]

    for route, payload in requests:
        response = client.post(route, content=payload, headers={"content-type": "application/json"})
        assert response.status_code == 422, (route, response.text)


def test_solve_rejects_non_finite_nested_water_osmosis() -> None:
    response = TestClient(api_app.app).post(
        "/solve",
        content='{"water_profile": {"mg_per_l": {}, "osmosis_percent": Infinity}}',
        headers={"content-type": "application/json"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid osmosis_percent value"


def test_resource_list_skips_invalid_yaml(monkeypatch, tmp_path, caplog) -> None:
    layout = api_app._portable_layout()
    monkeypatch.setattr(api_app, "PORTABLE_LAYOUT", replace(layout, recipes=tmp_path))
    (tmp_path / "good.yml").write_text("name: Good\nliters: 10\n", encoding="utf-8")
    (tmp_path / "broken.yml").write_text("name: [", encoding="utf-8")

    response = TestClient(api_app.app).get("/recipes")

    assert response.status_code == 200
    assert response.json() == [{"name": "Good", "filename": "good.yml"}]
    assert "Skipping invalid YAML resource" in caplog.text
