import json
from pathlib import Path
from shutil import copy2

import pytest
from fastapi.testclient import TestClient

from horticalc.core import compute_solution
from horticalc.data_io import load_fertilizers, load_molar_masses, load_recipe

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / "recipes/imports/manifest.json").read_text(encoding="utf-8"))
PHASES = [phase for program in MANIFEST["programs"] for phase in program["recipes"]]
ACTIVE = [phase for phase in PHASES if phase["active"]]


@pytest.fixture(scope="module")
def calculation_data():
    return load_fertilizers(ROOT / "data/fertilizers.csv"), load_molar_masses(ROOT / "data/molar_masses.yml")


def test_every_recipe_ingredient_has_a_product_record() -> None:
    names = {product["catalog_name"] for product in MANIFEST["products"]}
    assert {row["name"] for phase in PHASES for row in phase["recipe"]["fertilizers"]} <= names


@pytest.mark.parametrize("phase", ACTIVE, ids=lambda phase: Path(phase["file"]).stem)
def test_manufacturer_recipe_resolves_ingredients_and_scales(phase, calculation_data) -> None:
    catalogue, masses = calculation_data
    path = ROOT / phase["file"]
    assert path.parent == ROOT / "recipes"
    assert not phase["blockers"] and not phase["unmodeled_rows"]
    recipe = load_recipe(path)
    assert recipe == phase["recipe"]

    actual = compute_solution(recipe, catalogue, masses, {}).to_dict()
    scaled_recipe = dict(
        recipe,
        liters=recipe["liters"] * 2,
        fertilizers=[dict(row, grams=row["grams"] * 2) for row in recipe["fertilizers"]],
    )
    scaled = compute_solution(scaled_recipe, catalogue, masses, {}).to_dict()

    assert scaled["elements_mg_per_l"] == pytest.approx(actual["elements_mg_per_l"])
    assert scaled["fertilizer_oxides_mg_per_l"] == pytest.approx(actual["fertilizer_oxides_mg_per_l"])


def test_recipe_selector_contains_active_imports_and_excludes_pending_files(
    api_client: TestClient, isolated_app_root: Path
) -> None:
    pending = next(phase for phase in PHASES if not phase["active"])
    pending_path = isolated_app_root / pending["file"]
    pending_path.parent.mkdir(parents=True)
    copy2(ROOT / pending["file"], pending_path)

    response = api_client.get("/recipes")
    assert response.status_code == 200
    filenames = {row["filename"] for row in response.json()}

    assert {Path(phase["file"]).name for phase in ACTIVE} <= filenames
    for phase in PHASES:
        if not phase["active"]:
            assert (ROOT / phase["file"]).parent != ROOT / "recipes"
            assert phase["blockers"]
            assert Path(phase["file"]).name not in filenames


def test_plagron_coco_includes_hydro_roots_declared_nutrients(calculation_data) -> None:
    catalogue, masses = calculation_data
    recipe = load_recipe(ROOT / "recipes/plagron_coco_de_systemfeeding_01.yml")

    result = compute_solution(recipe, catalogue, masses, {}).to_dict()

    assert result["elements_mg_per_l"]["N_total"] == pytest.approx(69.375)
    assert result["oxides_mg_per_l"]["P2O5"] == pytest.approx(329.645)
    assert result["elements_mg_per_l"]["B"] == pytest.approx(0.508)


def test_ghf_regional_recipe_uses_its_own_analysis(calculation_data) -> None:
    catalogue, masses = calculation_data
    recipe = load_recipe(ROOT / "recipes/ghf_uk_au_2019_short_flowering_soil_01.yml")

    result = compute_solution(recipe, catalogue, masses, {}).to_dict()

    assert recipe["fertilizers"][0]["name"] == "Green House Feeding Grow (UK-AU 2019)"
    assert result["elements_mg_per_l"]["N_total"] == pytest.approx(144.0)
    assert result["elements_mg_per_l"]["Ca"] == pytest.approx(45.0, abs=0.02)


def test_floraflex_label_recipe_uses_its_printed_liter_basis(calculation_data) -> None:
    catalogue, masses = calculation_data
    recipe = load_recipe(ROOT / "recipes/floraflex_us_label_vegetative_4l_01.yml")

    result = compute_solution(recipe, catalogue, masses, {}).to_dict()

    assert recipe["liters"] == 4.0
    assert result["elements_mg_per_l"]["N_total"] == pytest.approx(50.0)
    assert result["elements_mg_per_l"]["Ca"] == pytest.approx(37.5)
    assert result["oxides_mg_per_l"]["P2O5"] == pytest.approx(42.5)


def test_floraflex_simple_chart_uses_us_gallon(calculation_data) -> None:
    catalogue, masses = calculation_data
    recipe = load_recipe(ROOT / "recipes/floraflex_us_supersimple_nocalmag_high_01.yml")
    result = compute_solution(recipe, catalogue, masses, {}).to_dict()

    assert recipe["liters"] == 3.785411784
    assert result["elements_mg_per_l"]["N_total"] == pytest.approx(264.1720524)


def test_atami_wsp_c_uses_full_analysis_instead_of_npk_short_name(calculation_data) -> None:
    catalogue, masses = calculation_data
    recipe = {"liters": 1.0, "fertilizers": [{"name": "Atami WSP C", "grams": 1.0}]}

    result = compute_solution(recipe, catalogue, masses, {}).to_dict()

    assert result["elements_mg_per_l"]["N_total"] == pytest.approx(13.0)
    assert result["oxides_mg_per_l"]["P2O5"] == pytest.approx(291.0)
    assert result["oxides_mg_per_l"]["K2O"] == pytest.approx(384.0)


def test_atami_led_optional_flush_retains_printed_nutrient_doses(calculation_data) -> None:
    catalogue, masses = calculation_data
    recipe = load_recipe(ROOT / "recipes/atami_wsp_direct_various_ec_led_heavy_07.yml")

    result = compute_solution(recipe, catalogue, masses, {}).to_dict()

    assert recipe["liters"] == 10.0
    assert {row["name"]: row["grams"] for row in recipe["fertilizers"]} == {
        "Atami WSP A": 2.7,
        "Atami WSP B": 2.5,
        "Atami WSP C": 2.3,
    }
    assert result["elements_mg_per_l"]["N_total"] == pytest.approx(55.59)


@pytest.mark.parametrize(
    ("name", "phosphate", "potash"),
    [
        ("Atami Bloombastic", 196.0, 210.0),
        ("Atami Rokzbastic", 147.5, 295.0),
        ("Atami ATA PK 13-14", 163.8, 176.4),
        ("Atami B’cuzz Hydro B", 45.2, 67.8),
        ("Atami B’cuzz Soil B", 33.0, 44.0),
        ("Atami B’cuzz Blossom Builder Liquid", 262.8, 335.8),
        ("Atami B’cuzz Blossom Builder Tabzz", 320.0, 200.0),
    ],
)
def test_atami_de_declared_pk_uses_mass_basis_and_density(calculation_data, name, phosphate, potash) -> None:
    catalogue, masses = calculation_data
    recipe = {"liters": 1.0, "fertilizers": [{"name": name, "grams": 1.0}]}

    result = compute_solution(recipe, catalogue, masses, {}).to_dict()

    assert result["oxides_mg_per_l"]["P2O5"] == pytest.approx(phosphate)
    assert result["oxides_mg_per_l"]["K2O"] == pytest.approx(potash)


def test_athena_us_label_grow_uses_label_density(calculation_data) -> None:
    catalogue, masses = calculation_data
    recipe = load_recipe(ROOT / "recipes/athena_us_label_grow_10l_01.yml")
    result = compute_solution(recipe, catalogue, masses, {}).to_dict()

    assert recipe["liters"] == 10.0
    assert result["elements_mg_per_l"]["N_total"] == pytest.approx(29.6869974)
    assert result["elements_mg_per_l"]["Ca"] == pytest.approx(25.16355, abs=0.001)


def test_floraflex_b2_label_distinguishes_magnesium_from_calcium(calculation_data) -> None:
    catalogue, masses = calculation_data
    fertilizer = catalogue["FloraFlex B2 (US label)"]
    recipe = {"liters": 1.0, "fertilizers": [{"name": fertilizer.name, "grams": 1.0}]}

    result = compute_solution(recipe, catalogue, masses, {}).to_dict()

    assert "CaO" not in fertilizer.comp
    assert result["elements_mg_per_l"]["Mg"] == pytest.approx(70.0)
    assert result["elements_mg_per_l"]["S"] == pytest.approx(110.0)


def test_drypart_grow_retains_declared_nitrogen_forms(calculation_data) -> None:
    catalogue, masses = calculation_data
    recipe = {"liters": 10.0, "fertilizers": [{"name": "T.A. DryPart Grow FR FREN70102", "grams": 2.0}]}

    result = compute_solution(recipe, catalogue, masses, {}).to_dict()

    assert result["elements_mg_per_l"]["N_total"] == pytest.approx(24.0)
    assert result["elements_mg_per_l"]["N_NO3"] == pytest.approx(21.0)
    assert result["elements_mg_per_l"]["N_NH4"] == pytest.approx(3.0)


def test_bac_liquid_declaration_uses_mass_percentages_and_density(calculation_data) -> None:
    catalogue, masses = calculation_data
    recipe = {"liters": 1.0, "fertilizers": [{"name": "BAC 1 Component Grow (EN SDS)", "grams": 1.0}]}

    result = compute_solution(recipe, catalogue, masses, {}).to_dict()

    assert result["elements_mg_per_l"]["N_total"] == pytest.approx(71.63)
    assert result["elements_mg_per_l"]["N_NO3"] == pytest.approx(62.814)
    assert result["elements_mg_per_l"]["N_NH4"] == pytest.approx(8.816)
    assert result["elements_mg_per_l"]["Fe"] == pytest.approx(0.30856)


def test_bac_calmag_preserves_printed_magnesium_value(calculation_data) -> None:
    catalogue, masses = calculation_data
    recipe = {"liters": 1.0, "fertilizers": [{"name": "BAC Calmag 2.0 (EN SDS)", "grams": 1.0}]}

    result = compute_solution(recipe, catalogue, masses, {}).to_dict()

    assert result["elements_mg_per_l"]["N_total"] == pytest.approx(66.12)
    assert result["elements_mg_per_l"]["Ca"] == pytest.approx(55.1)
    assert result["elements_mg_per_l"]["Mg"] == pytest.approx(132.24)


@pytest.mark.parametrize(
    ("name", "nitrogen", "unresolved_percent"),
    [
        ("BAC Organic Grow (EN SDS)", 53.3, 4.1),
        ("BAC Organic Bloom (EN SDS)", 78.0, 0.2),
        ("BAC Organic PK Booster (EN SDS)", 27.3, 2.1),
    ],
)
def test_bac_organic_profiles_only_count_declared_nitrate(calculation_data, name, nitrogen, unresolved_percent) -> None:
    catalogue, masses = calculation_data
    recipe = {"liters": 1.0, "fertilizers": [{"name": name, "grams": 1.0}]}

    result = compute_solution(recipe, catalogue, masses, {}).to_dict()

    assert result["elements_mg_per_l"]["N_total"] == pytest.approx(nitrogen)
    assert result["elements_mg_per_l"]["N_NO3"] == pytest.approx(nitrogen)
    product = next(product for product in MANIFEST["products"] if product["catalog_name"] == name)
    assert product["raw_unresolved_n_difference_percent"] == pytest.approx(unresolved_percent)
    assert product["readiness_scope"] == "declared_nutrient_contributions_only"


def test_dutchpro_massive_powder_uses_per_100g_declaration(calculation_data) -> None:
    catalogue, masses = calculation_data
    recipe = {"liters": 1.0, "fertilizers": [{"name": "Dutchpro Massive Powder Shot EU", "grams": 1.0}]}

    result = compute_solution(recipe, catalogue, masses, {}).to_dict()

    assert result["oxides_mg_per_l"]["P2O5"] == pytest.approx(520.0)
    assert result["oxides_mg_per_l"]["K2O"] == pytest.approx(340.0)


def test_plagron_silic_rock_keeps_organic_nitrogen_out_of_mineral_totals(calculation_data) -> None:
    catalogue, masses = calculation_data
    recipe = {"liters": 1.0, "fertilizers": [{"name": "Plagron Silic Rock", "grams": 1.0}]}

    result = compute_solution(recipe, catalogue, masses, {}).to_dict()

    assert result["elements_mg_per_l"]["N_total"] == pytest.approx(5.4)
    assert result["oxides_mg_per_l"]["K2O"] == pytest.approx(18.36)
    assert result["oxides_mg_per_l"]["SiO2"] == pytest.approx(11.88)
    product = next(p for p in MANIFEST["products"] if p["catalog_name"] == "Plagron Silic Rock")
    assert product["raw_nutrients"]["N_organic"]["value"] == 1.0
    assert "organic" in product["information"].lower()


def test_partial_organic_profiles_do_not_release_complete_manufacturer_phases() -> None:
    phases = [
        phase
        for phase in PHASES
        if any(row["name"] in {"Plagron Power Buds", "Plagron Silic Rock"} for row in phase["recipe"]["fertilizers"])
    ]
    assert phases
    for phase in phases:
        if phase["active"]:
            assert "declared mineral contributions" in phase["recipe"]["name"]
            assert "Organic" in phase["calculation_scope"] or "organic" in phase["calculation_scope"]
        else:
            assert phase["blockers"]


def test_ta_silicate_retains_declared_total_mass_contributions(calculation_data) -> None:
    catalogue, masses = calculation_data
    name = "T.A. Silicate FR (declared total contents)"
    recipe = {"liters": 1.0, "fertilizers": [{"name": name, "grams": 1.0}]}

    result = compute_solution(recipe, catalogue, masses, {}).to_dict()

    assert result["oxides_mg_per_l"]["CaO"] == pytest.approx(134.6)
    assert result["oxides_mg_per_l"]["MgO"] == pytest.approx(29.5)
    assert result["elements_mg_per_l"]["Fe"] == pytest.approx(24.0)


def test_bac_conflicting_nitrogen_declaration_stays_out_of_catalogue(calculation_data) -> None:
    catalogue, _ = calculation_data
    assert "BAC Coco Bloom A (EN SDS)" not in catalogue
    product = next(p for p in MANIFEST["products"] if p["catalog_name"] == "BAC Coco Bloom A (EN SDS)")
    assert product["ready"] is False
    assert product["comp"] is None
    assert product["raw_declared_percent"]["N_total"] == 10.0
    assert product["raw_declared_percent"]["NO3"] == 9.4
    assert product["raw_declared_percent"]["NH4"] == 0.7
    assert product["blockers"]


@pytest.mark.parametrize(
    ("medium", "dose", "nitrogen", "potassium_oxide"),
    [("hydro_coco", 20.0, 44.0, 514.0), ("soil", 15.0, 33.0, 385.5)],
)
def test_hyperbloom_recipe_uses_fr_guaranteed_analysis(
    calculation_data, medium, dose, nitrogen, potassium_oxide
) -> None:
    catalogue, masses = calculation_data
    recipe = load_recipe(ROOT / f"recipes/t_a_drypart_fr_2025_{medium}_easy_hyperbloom_06.yml")

    result = compute_solution(recipe, catalogue, masses, {}).to_dict()

    assert recipe["fertilizers"] == [{"name": "T.A. HyperBloom FR FREN72111 (guaranteed analysis)", "grams": dose}]
    assert result["elements_mg_per_l"]["N_total"] == pytest.approx(nitrogen)
    assert result["elements_mg_per_l"]["N_NH4"] == pytest.approx(nitrogen)
    assert result["oxides_mg_per_l"]["K2O"] == pytest.approx(potassium_oxide)


def test_hyperbloom_expert_additives_remain_blocked() -> None:
    phases = [
        phase
        for program in MANIFEST["programs"]
        if "drypart_fr_2025" in program["id"] and "expert" in program["id"] and "hyperbloom" in program["id"]
        for phase in program["recipes"]
        if phase["phase"] == "Ripening"
    ]

    assert len(phases) == 8
    assert all(not phase["active"] for phase in phases)
    assert all(
        any("HyperBloom must be used alone according to the FR product description" in b for b in p["blockers"])
        for p in phases
    )


def test_drypart_bloom_uses_label_confirmed_magnesium(calculation_data) -> None:
    catalogue, masses = calculation_data
    recipe = {"liters": 10.0, "fertilizers": [{"name": "T.A. DryPart Bloom FR FREN71102", "grams": 18.0}]}
    result = compute_solution(recipe, catalogue, masses, {}).to_dict()

    assert result["elements_mg_per_l"]["N_total"] == pytest.approx(108.0)
    assert result["oxides_mg_per_l"]["MgO"] == pytest.approx(126.0)
    product = next(p for p in MANIFEST["products"] if p["catalog_name"] == "T.A. DryPart Bloom FR FREN71102")
    assert product["ready"] is True
    assert product["label_review"]["visual_reviewed"] is True
    assert any("7.Trioxyde" in field["value"] for field in product["raw_features"])
