from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from horticalc.core import compute_solution
from horticalc.data_io import load_fertilizers, load_molar_masses, load_recipe

ROOT = Path(__file__).resolve().parents[1]
MANUFACTURER_RECIPES = sorted(
    path for path in (ROOT / "recipes").glob("*.yml") if "# Source SHA-256:" in path.read_text(encoding="utf-8")
)


@pytest.fixture(scope="module")
def calculation_data():
    return load_fertilizers(ROOT / "data/fertilizers.csv"), load_molar_masses(ROOT / "data/molar_masses.yml")


@pytest.mark.parametrize("path", MANUFACTURER_RECIPES, ids=lambda path: path.stem)
def test_manufacturer_recipe_resolves_ingredients_and_scales(path, calculation_data) -> None:
    catalogue, masses = calculation_data
    recipe = load_recipe(path)
    assert {row["name"] for row in recipe["fertilizers"]} <= catalogue.keys()

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
    nested_recipe = isolated_app_root / "recipes/imports/local_reference.yml"
    nested_recipe.parent.mkdir()
    nested_recipe.write_text("name: Local reference\nliters: 10\n", encoding="utf-8")

    response = api_client.get("/recipes")
    assert response.status_code == 200
    filenames = {row["filename"] for row in response.json()}
    assert MANUFACTURER_RECIPES
    assert {path.name for path in MANUFACTURER_RECIPES} <= filenames
    assert nested_recipe.name not in filenames


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
    ("name", "nitrogen"),
    [
        ("BAC Organic Grow (EN SDS)", 53.3),
        ("BAC Organic Bloom (EN SDS)", 78.0),
        ("BAC Organic PK Booster (EN SDS)", 27.3),
    ],
)
def test_bac_organic_profiles_only_count_declared_nitrate(calculation_data, name, nitrogen) -> None:
    catalogue, masses = calculation_data
    recipe = {"liters": 1.0, "fertilizers": [{"name": name, "grams": 1.0}]}

    result = compute_solution(recipe, catalogue, masses, {}).to_dict()

    assert result["elements_mg_per_l"]["N_total"] == pytest.approx(nitrogen)
    assert result["elements_mg_per_l"]["N_NO3"] == pytest.approx(nitrogen)


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


def test_power_buds_recipes_identify_their_calculation_scope() -> None:
    recipes = [load_recipe(path) for path in MANUFACTURER_RECIPES]
    using_power_buds = [
        recipe for recipe in recipes if any(row["name"] == "Plagron Power Buds" for row in recipe["fertilizers"])
    ]
    assert using_power_buds
    assert all("declared mineral contributions" in recipe["name"] for recipe in using_power_buds)


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


def test_drypart_bloom_uses_label_confirmed_magnesium(calculation_data) -> None:
    catalogue, masses = calculation_data
    recipe = {"liters": 10.0, "fertilizers": [{"name": "T.A. DryPart Bloom FR FREN71102", "grams": 18.0}]}
    result = compute_solution(recipe, catalogue, masses, {}).to_dict()

    assert result["elements_mg_per_l"]["N_total"] == pytest.approx(108.0)
    assert result["oxides_mg_per_l"]["MgO"] == pytest.approx(126.0)
