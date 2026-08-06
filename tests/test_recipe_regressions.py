from pathlib import Path

import pytest

from horticalc.core import run_recipe
from horticalc.data_io import load_molar_masses, load_recipe

ROOT = Path(__file__).resolve().parents[1]
RECIPES = ROOT / "recipes"
REFERENCE_RECIPE_NAMES = (
    "reference_agrolution_313_1g_per_l.yml",
    "reference_calcinit_1g_per_l.yml",
    "reference_calcinit_epso_top_1g_per_l_each.yml",
)


def _run(name: str) -> dict:
    return run_recipe(RECIPES / name)


def test_shipped_reference_recipes_use_zero_water_and_one_gram_per_liter() -> None:
    default = load_recipe(RECIPES / "default.yml")
    assert default["osmosis_percent"] == 0
    assert default["fertilizers"] == []

    for name in REFERENCE_RECIPE_NAMES:
        path = RECIPES / name
        recipe = load_recipe(path)
        assert recipe["osmosis_percent"] == 100
        liters = float(recipe["liters"])
        assert recipe["fertilizers"]
        assert all(float(entry["grams"]) / liters == pytest.approx(1.0) for entry in recipe["fertilizers"])


def test_calcinit_one_gram_per_liter_matches_declared_analysis() -> None:
    result = _run("reference_calcinit_1g_per_l.yml")

    assert result["oxides_mg_per_l"]["CaO"] == pytest.approx(260.0)
    assert result["elements_mg_per_l"]["N_NO3"] == pytest.approx(144.0)
    assert result["elements_mg_per_l"]["N_NH4"] == pytest.approx(11.0)
    assert result["elements_mg_per_l"]["N_total"] == pytest.approx(155.0)

    mm = load_molar_masses()
    expected_ca = 260.0 * mm["Ca"] / mm["CaO"]
    assert result["elements_mg_per_l"]["Ca"] == pytest.approx(expected_ca)


def test_calcinit_and_epso_top_one_gram_per_liter_each_add_linearly() -> None:
    result = _run("reference_calcinit_epso_top_1g_per_l_each.yml")
    oxides = result["oxides_mg_per_l"]

    assert oxides["CaO"] == pytest.approx(260.0)
    assert oxides["MgO"] == pytest.approx(160.0)
    assert oxides["SO4"] == pytest.approx(389.5)
    assert result["elements_mg_per_l"]["N_total"] == pytest.approx(155.0)

    mm = load_molar_masses()
    assert result["elements_mg_per_l"]["Mg"] == pytest.approx(160.0 * mm["Mg"] / mm["MgO"])
    assert result["elements_mg_per_l"]["S"] == pytest.approx(389.5 * mm["S"] / mm["SO4"])


def test_agrolution_313_one_gram_per_liter_matches_declared_analysis() -> None:
    result = _run("reference_agrolution_313_1g_per_l.yml")
    oxides = result["oxides_mg_per_l"]
    elements = result["elements_mg_per_l"]

    assert oxides["P2O5"] == pytest.approx(70.0)
    assert oxides["K2O"] == pytest.approx(140.0)
    assert oxides["CaO"] == pytest.approx(140.0)
    assert elements["N_NO3"] == pytest.approx(117.0)
    assert elements["N_UREA"] == pytest.approx(23.0)
    assert elements["N_total"] == pytest.approx(140.0)
    assert {key: elements[key] for key in ("Fe", "Mn", "Cu", "Zn", "B", "Mo")} == pytest.approx(
        {"Fe": 1.6, "Mn": 1.6, "Cu": 0.1, "Zn": 0.1, "B": 0.1, "Mo": 0.1}
    )

    mm = load_molar_masses()
    assert elements["P"] == pytest.approx(70.0 * 2.0 * mm["P"] / mm["P2O5"])
    assert elements["K"] == pytest.approx(140.0 * 2.0 * mm["K"] / mm["K2O"])
    assert elements["Ca"] == pytest.approx(140.0 * mm["Ca"] / mm["CaO"])
