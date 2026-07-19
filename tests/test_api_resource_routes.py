import pytest
from fastapi.testclient import TestClient

import api.app as api_app
from horticalc import paths


def test_unit_schema_exposes_canonical_volume_and_explicit_gallons() -> None:
    response = TestClient(api_app.app).get("/schema/units")

    assert response.status_code == 200
    payload = response.json()
    assert payload["canonical_volume_unit"] == "liter"
    assert payload["canonical_solid_dose_unit"] == "gram"
    assert payload["canonical_liquid_dose_unit"] == "milliliter"
    units = {entry["key"]: entry for entry in payload["volume_units"]}
    assert units["us_gallon"]["liters_per_unit"] == pytest.approx(3.785411784)
    assert units["imperial_gallon"]["liters_per_unit"] == pytest.approx(4.54609)
    mass_units = {entry["key"]: entry for entry in payload["mass_units"]}
    liquid_units = {entry["key"]: entry for entry in payload["liquid_volume_units"]}
    assert mass_units["ounce"]["grams_per_unit"] == pytest.approx(28.349523125)
    assert liquid_units["us_fluid_ounce"]["milliliters_per_unit"] == pytest.approx(29.5735295625)


def test_portable_layout_resource_routes() -> None:
    client = TestClient(api_app.app)

    responses = {
        "water profiles": client.get("/water-profiles"),
        "default water profile": client.get("/water-profiles/default"),
        "nutrient solutions": client.get("/nutrient-solutions"),
        "nutrient solution": client.get("/nutrient-solutions/Cooper_NFT_1979"),
        "default recipe": client.get("/recipes/default"),
        "recipe": client.get("/recipes/golden"),
    }

    assert {name: response.status_code for name, response in responses.items()} == dict.fromkeys(responses, 200)


def test_resource_routes_layer_user_yaml_over_shipped_defaults(monkeypatch, tmp_path) -> None:
    shipped_water = tmp_path / "data" / "water_profiles"
    shipped_targets = tmp_path / "data" / "nutrient_solutions"
    shipped_recipes = tmp_path / "recipes"
    for directory in (shipped_water, shipped_targets, shipped_recipes):
        directory.mkdir(parents=True)

    (shipped_water / "tap.yml").write_text(
        "name: Shipped tap\nmg_per_l: {}\n",
        encoding="utf-8",
    )
    (shipped_targets / "target.yml").write_text(
        "name: Shipped target\ntargets_mg_per_l: {}\n",
        encoding="utf-8",
    )
    (shipped_recipes / "default.yml").write_text(
        "name: Shipped default\nliters: 10\nfertilizers: []\n",
        encoding="utf-8",
    )
    (shipped_recipes / "golden.yml").write_text(
        "name: Shipped golden\nliters: 10\nfertilizers: []\n",
        encoding="utf-8",
    )

    user_water = paths.user_water_profiles_dir(tmp_path)
    user_targets = paths.user_nutrient_solutions_dir(tmp_path)
    user_recipes = paths.user_recipes_dir(tmp_path)
    for directory in (user_water, user_targets, user_recipes):
        directory.mkdir(parents=True)
    (user_water / "tap.yml").write_text(
        "name: User tap\nmg_per_l: {Ca: 42}\n",
        encoding="utf-8",
    )
    (user_targets / "custom.yml").write_text(
        "name: User target\ntargets_mg_per_l: {N_total: 100}\n",
        encoding="utf-8",
    )
    (user_recipes / "golden.yml").write_text(
        "name: User golden\nliters: 20\nfertilizers: []\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(api_app, "PORTABLE_LAYOUT", paths.ensure_portable_layout(tmp_path))
    client = TestClient(api_app.app)

    assert client.get("/water-profiles").json() == [{"name": "User tap", "filename": "tap.yml"}]
    assert {entry["filename"] for entry in client.get("/nutrient-solutions").json()} == {
        "custom.yml",
        "target.yml",
    }
    assert client.get("/water-profiles/tap").json()["mg_per_l"] == {"Ca": 42.0}
    assert client.get("/recipes/golden").json()["name"] == "User golden"
    assert client.get("/recipes/default").json()["name"] == "Shipped default"


def test_nutrient_solution_round_trips_directional_solver_priorities(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(api_app, "PORTABLE_LAYOUT", paths.ensure_portable_layout(tmp_path))
    client = TestClient(api_app.app)
    payload = {
        "name": "Prioritized target",
        "source": "Test",
        "targets_mg_per_l": {"N_total": 160, "Ca": 120},
        "solver_config": {
            "solver_model": "hierarchical",
            "target_priorities": {
                "N_total": {"under": 1, "over": 1},
                "Ca": {"under": 2, "over": 4},
            },
        },
    }

    save_response = client.post("/nutrient-solutions", json=payload)

    assert save_response.status_code == 200
    loaded = client.get("/nutrient-solutions/Prioritized_target")
    assert loaded.status_code == 200
    assert loaded.json() == payload


def test_nutrient_solution_rejects_invalid_directional_priority(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(api_app, "PORTABLE_LAYOUT", paths.ensure_portable_layout(tmp_path))

    response = TestClient(api_app.app).post(
        "/nutrient-solutions",
        json={
            "name": "Invalid priority",
            "targets_mg_per_l": {"N_total": 160},
            "solver_config": {
                "solver_model": "hierarchical",
                "target_priorities": {"N_total": {"under": 9}},
            },
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid target_priorities value: N_total.under"
