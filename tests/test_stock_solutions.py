from dataclasses import replace
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import api.app as api_app
from horticalc.data_io import Fertilizer, load_fertilizers, load_molar_masses, load_recipe, safe_load_yaml
from horticalc.stock_solutions import StockSettings, StockWater, material_fingerprint, plan_stock_solutions

ROOT = Path(__file__).resolve().parents[1]
CALCIUM = "Yara Tera CALCINIT"
MAGNESIUM = "K+S EPSO Top Bittersalz 16-39"
BLEND = "Agrolution Special 313 14-7-14+14CaO+TE"


@pytest.fixture
def materials():
    return load_fertilizers(ROOT / "data/fertilizers.csv")


def make_plan(materials, *, doses=None, settings=None, water=None, suggest=True):
    recipe = {
        "liters": 10,
        "fertilizers": doses or [{"name": CALCIUM, "grams": 10}, {"name": MAGNESIUM, "grams": 10}],
    }
    return plan_stock_solutions(
        recipe,
        water or StockWater(),
        settings or StockSettings(),
        materials,
        load_molar_masses(),
        suggest_assignments=suggest,
    )


def test_assignments_require_an_explicit_suggestion_or_manual_selection(materials):
    plan = make_plan(materials, suggest=False)
    assert not plan["complete"] and plan["final_solution"] is None
    assert not plan["exportable"]
    assert plan["settings"]["assignments"] == {CALCIUM: None, MAGNESIUM: None}
    assert plan["tanks"] == []


def test_two_stocks_preserve_fertilizer_delivery_and_displace_water(materials):
    plan = make_plan(materials, water=StockWater(mg_per_l={"Ca": 80}))
    assert plan["complete"]
    assert plan["exportable"]
    assert [tank["id"] for tank in plan["tanks"]] == ["A", "B"]
    for tank in plan["tanks"]:
        assert tank["ingredients"][0]["stock_amount"] == 100
        assert tank["dose_ml_per_l"] == 10
        assert tank["dose_ml"] == 100
        assert tank["capacity_liters"] == 100
    assert plan["final_solution"]["water_elements_mg_per_l"]["Ca"] == pytest.approx(78.4)
    assert plan["final_solution"]["fertilizer_elements_mg_per_l"]["N_total"] == pytest.approx(155)
    assert plan["makeup_water_liters"] == pytest.approx(9.8)


def test_duplicate_rows_and_independent_stock_sizes(materials):
    settings = StockSettings(tanks={"A": {"liters": 2, "factor": 50}, "B": {"liters": 1, "factor": 200}})
    plan = make_plan(
        materials,
        settings=settings,
        doses=[
            {"name": CALCIUM, "grams": 3},
            {"name": CALCIUM, "grams": 7},
            {"name": MAGNESIUM, "grams": 10},
        ],
    )
    assert len(plan["ingredients"]) == 2
    assert [tank["dose_ml"] for tank in plan["tanks"]] == [200, 50]
    assert [item["stock_amount"] for item in plan["ingredients"]] == [100, 200]


def test_liquid_requires_manual_assignment_and_density_is_applied_once(materials):
    materials["Custom liquid"] = Fertilizer("Custom liquid", True, 1.2, {"K2O": 0.1})
    doses = [{"name": "Custom liquid", "grams": 10}]
    draft = make_plan(materials, doses=doses)
    assert not draft["complete"] and draft["final_solution"] is None
    plan = make_plan(materials, doses=doses, settings=StockSettings(assignments={"Custom liquid": "A"}))
    assert plan["ingredients"][0]["unit"] == "mL"
    assert plan["ingredients"][0]["stock_amount"] == 100
    assert plan["final_solution"]["fertilizer_oxides_mg_per_l"]["K2O"] == pytest.approx(120)


def test_manual_assignment_is_not_overwritten_and_pair_risk_stays_visible(materials):
    settings = StockSettings(assignments={CALCIUM: "A", MAGNESIUM: "A"})
    plan = make_plan(materials, settings=settings)
    assert plan["complete"]
    assert plan["exportable"]
    assert plan["settings"]["assignments"] == settings.assignments
    risk = next(f for f in plan["findings"] if f["code"] == "pair_risk")
    assert set(risk["materials"]) == {CALCIUM, MAGNESIUM}
    assert risk["risks"] == ["calcium_sulfate"]
    assert risk["severity"] == "review"


def test_manufactured_calcium_phosphorus_blend_is_one_material(materials):
    plan = make_plan(materials, doses=[{"name": BLEND, "grams": 10}])
    assert plan["complete"] and len(plan["tanks"]) == 1
    assert plan["findings"] == []
    assert plan["ingredients"][0]["stock_amount"] == 100


def test_blend_with_added_sulfate_has_a_cross_product_risk(materials):
    plan = make_plan(
        materials,
        doses=[{"name": BLEND, "grams": 10}, {"name": MAGNESIUM, "grams": 10}],
        settings=StockSettings(assignments={BLEND: "A", MAGNESIUM: "A"}),
    )
    risks = [f for f in plan["findings"] if f["code"] == "pair_risk"]
    assert len(risks) == 1
    assert set(risks[0]["materials"]) == {BLEND, MAGNESIUM}
    assert "calcium_sulfate" in risks[0]["risks"]


@pytest.mark.parametrize(
    ("left_comp", "right_comp", "reason"),
    [
        ({"MgO": 0.16, "NO3": 0.11}, {"P2O5": 0.52}, "magnesium_phosphorus"),
        ({"CaO": 0.26}, {"HCO3": 0.5}, "carbonate"),
        ({"SiO2": 0.2}, {"K2O": 0.3}, "silicon"),
    ],
)
def test_other_declared_pair_risks_are_advisory(materials, left_comp, right_comp, reason):
    materials["First product"] = Fertilizer("First product", False, 1, left_comp)
    materials["Second product"] = Fertilizer("Second product", False, 1, right_comp)
    plan = make_plan(
        materials,
        doses=[{"name": name, "grams": 1} for name in ("First product", "Second product")],
        settings=StockSettings(assignments={"First product": "A", "Second product": "A"}),
    )
    assert plan["complete"] and plan["final_solution"] is not None
    assert reason in next(f for f in plan["findings"] if f["code"] == "pair_risk")["risks"]


def test_suggestions_work_for_new_catalog_products_and_are_order_independent(materials):
    name = "Additional sulfate product"
    materials[name] = Fertilizer(name, False, 1, {"K2O": 0.52, "SO4": 0.5})
    doses = [{"name": CALCIUM, "grams": 10}, {"name": name, "grams": 1}]
    forward = make_plan(materials, doses=doses)
    reverse = make_plan(materials, doses=list(reversed(doses)))
    assert forward["settings"]["assignments"] == reverse["settings"]["assignments"]
    assert forward["settings"]["assignments"][CALCIUM] != forward["settings"]["assignments"][name]


def test_trace_blend_and_phosphorus_do_not_create_a_missing_metadata_warning_or_force_separation(materials):
    trace = "Compo Fetrilon Combi 1"
    phosphorus = "ICL Nova PeKacid 0-60-20"
    doses = [{"name": name, "grams": 1} for name in (trace, phosphorus)]
    suggested = make_plan(materials, doses=doses)
    assert suggested["complete"] and len(suggested["tanks"]) == 1
    assert suggested["findings"] == []
    manual = make_plan(materials, doses=doses, settings=StockSettings(assignments={trace: "B", phosphorus: "B"}))
    assert manual["findings"] == []
    assert manual["settings"]["assignments"] == {trace: "B", phosphorus: "B"}


def test_suggestions_prefer_separation_for_conditional_risks_without_requiring_another_tank(materials):
    materials["Magnesium nitrate"] = Fertilizer("Magnesium nitrate", False, 1, {"MgO": 0.16, "NO3": 0.11})
    materials["Phosphorus fertilizer"] = Fertilizer("Phosphorus fertilizer", False, 1, {"P2O5": 0.52})
    doses = [{"name": name, "grams": 1} for name in ("Magnesium nitrate", "Phosphorus fertilizer")]
    plan = make_plan(materials, doses=doses)
    assert plan["complete"] and len(plan["tanks"]) == 2
    assert plan["findings"] == []
    single = make_plan(materials, doses=doses, settings=StockSettings(tanks={"A": {}}))
    assert single["complete"] and len(single["tanks"]) == 1
    assert "magnesium_phosphorus" in single["findings"][0]["risks"]


def test_suggestions_leave_unplaceable_products_open_until_c_is_available(materials):
    name = "Silicon powder"
    materials[name] = Fertilizer(name, False, 1, {"SiO2": 0.2})
    doses = [{"name": CALCIUM, "grams": 10}, {"name": MAGNESIUM, "grams": 10}, {"name": name, "grams": 0.5}]
    draft = make_plan(materials, doses=doses)
    assert not draft["complete"]
    assert draft["settings"]["assignments"][name] is None
    plan = make_plan(materials, doses=doses, settings=StockSettings(tanks={"A": {}, "B": {}, "C": {}}))
    assert plan["complete"]
    assert plan["settings"]["assignments"][name] == "C"


def test_changed_material_definition_requires_reassessment(materials):
    fingerprint = material_fingerprint(materials[CALCIUM])
    materials[CALCIUM] = replace(materials[CALCIUM], comp={"CaO": 0.1, "P2O5": 0.1})
    settings = StockSettings(assignments={CALCIUM: "A", MAGNESIUM: "B"}, material_fingerprints={CALCIUM: fingerprint})
    plan = make_plan(materials, settings=settings)
    repeated = make_plan(materials, settings=StockSettings.model_validate(plan["settings"]))
    for result in (plan, repeated):
        assert result["complete"] and not result["exportable"]
        assert result["settings"]["material_fingerprints"][CALCIUM] == fingerprint
        changed = next(f for f in result["findings"] if f["code"] == "material_changed")
        assert changed["materials"] == [CALCIUM]
        assert changed["fingerprint"] == material_fingerprint(materials[CALCIUM])
    reviewed = StockSettings.model_validate(repeated["settings"])
    reviewed.material_fingerprints[CALCIUM] = changed["fingerprint"]
    accepted = make_plan(materials, settings=reviewed)
    assert accepted["exportable"]
    assert not any(f["code"] == "material_changed" for f in accepted["findings"])
    materials[CALCIUM] = replace(materials[CALCIUM], comp={"CaO": 0.2})
    changed_again = make_plan(materials, settings=reviewed)
    assert not changed_again["exportable"]
    assert any(f["code"] == "material_changed" for f in changed_again["findings"])


def test_insufficient_stock_blocks_export_until_finished_volume_is_increased(materials):
    settings = StockSettings(tanks={"C": {"liters": 0.001, "factor": 100}}, assignments={CALCIUM: "C"})
    doses = [{"name": CALCIUM, "grams": 10}]
    short = make_plan(materials, doses=doses, settings=settings)
    assert short["complete"] and short["final_solution"] is not None
    assert not short["exportable"]
    assert short["tanks"][0]["dose_ml"] == 100
    assert any(f["code"] == "insufficient_stock" for f in short["findings"])
    settings.tanks["C"].liters = 0.1
    sufficient = make_plan(materials, doses=doses, settings=settings)
    assert sufficient["exportable"]
    assert sufficient["tanks"][0]["capacity_liters"] == 10
    assert not any(f["code"] == "insufficient_stock" for f in sufficient["findings"])


def test_exact_stock_capacity_accepts_decimal_volumes(api_client):
    recipe = {"liters": 29, "fertilizers": [{"name": CALCIUM, "grams": 29}]}
    settings = {"tanks": {"C": {"liters": 0.29, "factor": 100}}, "assignments": {CALCIUM: "C"}}
    response = api_client.post("/stock-solutions/plan", json={"recipe": recipe, "settings": settings})
    assert response.status_code == 200
    plan = response.json()
    assert plan["exportable"]
    assert plan["tanks"][0]["dose_ml"] == 290
    assert not any(f["code"] == "insufficient_stock" for f in plan["findings"])


def test_batch_scaling_preserves_stock_strength_and_checks_capacity(api_client):
    for liters in (10, 20, 5000):
        recipe = {
            "liters": liters,
            "fertilizers": [{"name": name, "grams": liters} for name in (CALCIUM, MAGNESIUM)],
            "water_mg_l": {"Ca": 80},
        }
        response = api_client.post("/stock-solutions/plan", json={"recipe": recipe, "suggest_assignments": True})
        assert response.status_code == 200
        plan = response.json()
        assert plan["complete"]
        assert plan["exportable"] is (liters <= 100)
        assert plan["final_solution"]["water_elements_mg_per_l"]["Ca"] == pytest.approx(78.4)
        assert plan["final_solution"]["fertilizer_elements_mg_per_l"]["N_total"] == pytest.approx(155)
        for tank in plan["tanks"]:
            assert tank["liters"] == 1
            assert tank["ingredients"][0]["stock_amount"] == 100
            assert tank["dose_ml_per_l"] == 10
            assert tank["dose_ml"] == liters * 10


def test_ro_mix_is_applied_once_and_all_stock_water_is_mineral_free(materials):
    plan = make_plan(materials, water=StockWater(mg_per_l={"Ca": 80}, osmosis_percent=50))
    assert plan["final_solution"]["water_elements_mg_per_l"]["Ca"] == pytest.approx(39.2)
    assert "preparation_water" not in plan["settings"]


@pytest.mark.parametrize(
    "settings",
    [
        {"tanks": {"A": {"factor": 1.5}, "B": {"factor": 1.5}}},
        {"assignments": {CALCIUM: "C"}},
        {"tanks": {"A": {"liters": 1e308, "factor": 100}}},
    ],
)
def test_impossible_preparations_fail_explicitly(materials, settings):
    with pytest.raises(ValueError):
        make_plan(materials, settings=StockSettings(**settings))


def test_api_and_recipe_round_trip(api_client, isolated_api_layout):
    recipe = {"liters": 10, "fertilizers": [{"name": CALCIUM, "grams": 10}], "water_mg_l": {"Ca": 80}}
    response = api_client.post("/stock-solutions/plan", json={"recipe": recipe, "suggest_assignments": True})
    assert response.status_code == 200
    plan = response.json()
    assert plan["final_solution"]["water_elements_mg_per_l"]["Ca"] == pytest.approx(79.2)
    assert "original_elements_mg_per_l" not in plan
    assert "difference_mg_per_l" not in plan
    attachment = plan["settings"]
    assert attachment["schema_version"] == 2
    saved = api_client.post("/recipes", json={**recipe, "name": "Stock example", "stock_solution": attachment})
    assert saved.status_code == 200
    loaded = api_client.get(f"/recipes/{saved.json()['filename']}")
    assert loaded.json()["stock_solution"] == attachment
    assert load_recipe(isolated_api_layout.recipes / saved.json()["filename"])["stock_solution"] == attachment


def test_stock_endpoints_require_desktop_session_and_same_origin(api_client):
    for endpoint in ("/stock-solutions/plan", "/stock-solutions/migrate-settings"):
        with TestClient(api_app.app, base_url="http://127.0.0.1") as anonymous:
            assert anonymous.post(endpoint, json={}).status_code == 403
        assert api_client.post(endpoint, json={}, headers={"Origin": "https://example.org"}).status_code == 403


@pytest.mark.parametrize(
    "settings",
    [
        {"source_water": {"mg_per_l": {"unknown": 1}}},
        {"material_fingerprints": {CALCIUM: "invalid"}},
        {"tanks": {"D": {}}},
        {"tanks": {"A": {"factor": 0}}},
        {"preparation_water": {"mg_per_l": {"Ca": 40}}},
        {"schema_version": 1},
    ],
)
def test_invalid_settings_return_validation_details(api_client, settings):
    recipe = {"liters": 10, "fertilizers": [{"name": CALCIUM, "grams": 10}]}
    planned = api_client.post("/stock-solutions/plan", json={"recipe": recipe, "settings": settings})
    assert planned.status_code == 422
    assert planned.json()["detail"][0]["loc"][1] == "settings"
    saved = api_client.post("/recipes", json={**recipe, "name": "Invalid stock", "stock_solution": settings})
    assert saved.status_code == 422


def test_saved_stock_attachment_is_migrated_once_with_original_backup(tmp_path):
    path = tmp_path / "stock.yml"
    original = "liters: 10\nstock_solution:\n  schema_version: 1\n  preparation_water: {mg_per_l: {}, osmosis_percent: 0}\n  temperature_c: 20\n  evidence_revision: old\n  assignments: {Yara Tera CALCINIT: A}\n"
    path.write_text(original, encoding="utf-8")
    loaded = load_recipe(path)
    assert loaded["stock_solution"]["schema_version"] == 2
    assert loaded["stock_solution"]["assignments"] == {CALCIUM: "A"}
    assert (tmp_path / "stock.yml.legacy-backup").read_text(encoding="utf-8") == original
    assert safe_load_yaml(path.read_text(encoding="utf-8")) == loaded
    assert load_recipe(path) == loaded
    assert len(list(tmp_path.glob("*.legacy-backup*"))) == 1


def test_mineralized_legacy_stock_water_is_not_silently_changed(tmp_path, api_client):
    path = tmp_path / "stock.yml"
    original = "liters: 10\nstock_solution:\n  schema_version: 1\n  preparation_water: {mg_per_l: {Ca: 40}, osmosis_percent: 0}\n"
    path.write_text(original, encoding="utf-8")
    with pytest.raises(ValueError, match="mineralized"):
        load_recipe(path)
    assert path.read_text(encoding="utf-8") == original
    assert not list(tmp_path.glob("*.legacy-backup*"))
    response = api_client.post(
        "/stock-solutions/migrate-settings", json={"settings": safe_load_yaml(original)["stock_solution"]}
    )
    assert response.status_code == 400
    assert "mineralized" in response.json()["detail"]


def test_explicit_snapshot_migration_preserves_source_water_and_assignments(api_client):
    settings = {
        "preparation_water": {"mg_per_l": {"Ca": 40}, "osmosis_percent": 100},
        "source_water": {"mg_per_l": {"Ca": 80}, "osmosis_percent": 66},
        "assignments": {CALCIUM: "B"},
    }
    response = api_client.post("/stock-solutions/migrate-settings", json={"settings": settings})
    assert response.status_code == 200
    assert response.json()["schema_version"] == 2
    assert response.json()["source_water"] == settings["source_water"]
    assert response.json()["assignments"] == settings["assignments"]
    assert "preparation_water" not in response.json()


def test_invalid_saved_stock_attachment_is_rejected(api_client, isolated_api_layout):
    path = isolated_api_layout.recipes / "invalid_stock.yml"
    path.write_text("liters: 10\nstock_solution:\n  schema_version: 2\n  tanks: {A: {factor: 0}}\n", encoding="utf-8")
    assert api_client.get("/recipes/invalid_stock.yml").status_code == 400
