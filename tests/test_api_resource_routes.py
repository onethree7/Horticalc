import pytest
from fastapi.testclient import TestClient

import api.app as api_app
from horticalc import paths


def test_unit_schema_exposes_canonical_volume_and_explicit_gallons(api_client: TestClient) -> None:
    response = api_client.get("/schema/units")

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


def test_portable_layout_resource_routes(api_client: TestClient) -> None:
    responses = {
        "water profiles": api_client.get("/water-profiles"),
        "default water profile": api_client.get("/water-profiles/default"),
        "nutrient solutions": api_client.get("/nutrient-solutions"),
        "nutrient solution": api_client.get("/nutrient-solutions/Cooper_NFT_1979"),
        "default recipe": api_client.get("/recipes/default"),
        "recipe": api_client.get("/recipes/golden"),
    }

    assert {name: response.status_code for name, response in responses.items()} == dict.fromkeys(responses, 200)


def test_resource_routes_layer_user_yaml_over_shipped_defaults(api_client: TestClient, monkeypatch, tmp_path) -> None:
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
    assert api_client.get("/water-profiles").json() == [{"name": "User tap", "filename": "tap.yml"}]
    assert {entry["filename"] for entry in api_client.get("/nutrient-solutions").json()} == {
        "custom.yml",
        "target.yml",
    }
    assert api_client.get("/water-profiles/tap").json()["mg_per_l"] == {"Ca": 42.0}
    assert api_client.get("/recipes/golden").json()["name"] == "User golden"
    assert api_client.get("/recipes/default").json()["name"] == "Shipped default"


def test_nutrient_solution_round_trips_directional_solver_priorities(
    api_client: TestClient, monkeypatch, tmp_path
) -> None:
    monkeypatch.setattr(api_app, "PORTABLE_LAYOUT", paths.ensure_portable_layout(tmp_path))
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

    save_response = api_client.post("/nutrient-solutions", json=payload)

    assert save_response.status_code == 200
    loaded = api_client.get("/nutrient-solutions/Prioritized_target")
    assert loaded.status_code == 200
    assert loaded.json() == payload


def test_nutrient_solution_persists_complete_solver_setup(api_client: TestClient, monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(api_app, "PORTABLE_LAYOUT", paths.ensure_portable_layout(tmp_path))
    payload = {
        "name": "Fixed micronutrients",
        "source": "Horticalc UI",
        "targets_mg_per_l": {"N_total": 100, "P": 10},
        "liters": 10,
        "water_profile": "default",
        "osmosis_percent": 20,
        "fertilizers_allowed": [
            "Compo Fetrilon Combi 1",
            "ICL Nova PeKacid 0-60-20",
        ],
        "fixed_grams": {
            "Compo Fetrilon Combi 1": 2,
            "ICL Nova PeKacid 0-60-20": 6,
        },
        "urea_as_nh4": False,
        "solver_config": {"solver_model": "mass_nnls"},
    }

    save_response = api_client.post("/nutrient-solutions", json=payload)

    assert save_response.status_code == 200
    loaded = api_client.get("/nutrient-solutions/Fixed_micronutrients")
    assert loaded.status_code == 200
    assert loaded.json() == payload


def test_nutrient_solution_without_setup_omits_setup_fields(api_client: TestClient, monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(api_app, "PORTABLE_LAYOUT", paths.ensure_portable_layout(tmp_path))
    payload = {
        "name": "Targets only",
        "source": "Horticalc UI",
        "targets_mg_per_l": {"K": 180},
    }

    assert api_client.post("/nutrient-solutions", json=payload).status_code == 200
    loaded = api_client.get("/nutrient-solutions/Targets_only")

    assert loaded.status_code == 200
    assert loaded.json() == payload


def test_nutrient_solution_requires_explicit_overwrite_and_preserves_existing_setup(
    api_client: TestClient, monkeypatch, tmp_path
) -> None:
    monkeypatch.setattr(api_app, "PORTABLE_LAYOUT", paths.ensure_portable_layout(tmp_path))
    setup_payload = {
        "name": "Protected target",
        "source": "",
        "targets_mg_per_l": {"K": 180},
        "liters": 10,
        "water_profile": "default",
        "osmosis_percent": 0,
        "fertilizers_allowed": ["A"],
        "fixed_grams": {"A": 2},
        "urea_as_nh4": False,
        "solver_config": {},
    }
    target_only_payload = {
        "name": "Protected target",
        "source": "",
        "targets_mg_per_l": {"K": 200},
    }

    assert api_client.post("/nutrient-solutions", json=setup_payload).status_code == 200
    conflict = api_client.post("/nutrient-solutions", json=target_only_payload)

    assert conflict.status_code == 409
    assert conflict.json()["detail"] == {
        "code": "nutrient_solution_exists",
        "name": "Protected target",
        "filename": "Protected_target.yml",
        "has_solver_setup": True,
    }
    assert api_client.get("/nutrient-solutions/Protected_target").json() == setup_payload

    overwritten = api_client.post(
        "/nutrient-solutions",
        json={**target_only_payload, "overwrite": True},
    )

    assert overwritten.status_code == 200
    assert api_client.get("/nutrient-solutions/Protected_target").json() == target_only_payload


def test_nutrient_solution_filename_collision_cannot_silently_replace_another_profile(
    api_client: TestClient, monkeypatch, tmp_path
) -> None:
    monkeypatch.setattr(api_app, "PORTABLE_LAYOUT", paths.ensure_portable_layout(tmp_path))
    original = {
        "name": "Collision/A",
        "source": "",
        "targets_mg_per_l": {"K": 180},
        "solver_config": {},
    }

    assert api_client.post("/nutrient-solutions", json=original).status_code == 200
    conflict = api_client.post(
        "/nutrient-solutions",
        json={"name": "Collision?A", "targets_mg_per_l": {"K": 200}},
    )

    assert conflict.status_code == 409
    assert conflict.json()["detail"] == {
        "code": "nutrient_solution_exists",
        "name": "Collision/A",
        "filename": "Collision_A.yml",
        "has_solver_setup": True,
    }
    assert api_client.get("/nutrient-solutions/Collision_A").json() == original


def test_nutrient_solution_rejects_fixed_amount_outside_allowed_list(
    api_client: TestClient,
    monkeypatch,
    tmp_path,
) -> None:
    monkeypatch.setattr(api_app, "PORTABLE_LAYOUT", paths.ensure_portable_layout(tmp_path))

    response = api_client.post(
        "/nutrient-solutions",
        json={
            "name": "Invalid fixed amount",
            "targets_mg_per_l": {"K": 180},
            "fertilizers_allowed": ["Allowed"],
            "fixed_grams": {"Other": 2},
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "fixed_grams not in fertilizers_allowed: ['Other']"


def test_nutrient_solution_rejects_duplicate_allowed_fertilizers(
    api_client: TestClient,
    monkeypatch,
    tmp_path,
) -> None:
    monkeypatch.setattr(api_app, "PORTABLE_LAYOUT", paths.ensure_portable_layout(tmp_path))

    response = api_client.post(
        "/nutrient-solutions",
        json={
            "name": "Duplicate fertilizers",
            "targets_mg_per_l": {"K": 180},
            "fertilizers_allowed": ["Repeated", "Repeated"],
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == ("fertilizers_allowed must not contain duplicates: ['Repeated']")


def test_nutrient_solution_rejects_empty_water_profile(api_client: TestClient, monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(api_app, "PORTABLE_LAYOUT", paths.ensure_portable_layout(tmp_path))

    response = api_client.post(
        "/nutrient-solutions",
        json={"name": "Invalid water", "water_profile": "   "},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "water_profile must be a non-empty string"


def test_nutrient_solution_rejects_invalid_directional_priority(api_client: TestClient, monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(api_app, "PORTABLE_LAYOUT", paths.ensure_portable_layout(tmp_path))

    response = api_client.post(
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
