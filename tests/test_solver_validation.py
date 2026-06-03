import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from horticalc.data_io import Fertilizer, load_molar_masses
from horticalc.solver import solve_recipe_data


def test_solve_recipe_data_rejects_invalid_target_key() -> None:
    molar_masses = load_molar_masses()
    ferts = {
        "K2O test": Fertilizer("K2O test", "fest", 1.0, {"K2O": 1.0}),
    }
    recipe = {
        "liters": 1,
        "water_profile": {"mg_per_l": {}},
        "fertilizers_allowed": ["K2O test"],
        "targets": {"K2O": 100.0},
    }

    with pytest.raises(ValueError, match="Invalid target key: K2O"):
        solve_recipe_data(recipe, ferts=ferts, mm=molar_masses)


def test_solve_recipe_data_rejects_non_positive_liters() -> None:
    molar_masses = load_molar_masses()
    ferts = {
        "K test": Fertilizer("K test", "fest", 1.0, {"K2O": 1.0}),
    }
    recipe = {
        "liters": 0,
        "water_profile": {"mg_per_l": {}},
        "fertilizers_allowed": ["K test"],
        "targets": {"K": 100.0},
    }

    with pytest.raises(ValueError, match="liters must be > 0"):
        solve_recipe_data(recipe, ferts=ferts, mm=molar_masses)


def test_solve_recipe_data_rejects_negative_fixed_grams() -> None:
    molar_masses = load_molar_masses()
    ferts = {
        "K test": Fertilizer("K test", "fest", 1.0, {"K2O": 1.0}),
    }
    recipe = {
        "liters": 1,
        "water_profile": {"mg_per_l": {}},
        "fertilizers_allowed": ["K test"],
        "fixed_grams": {"K test": -1.0},
        "targets": {"K": 100.0},
    }

    with pytest.raises(ValueError, match="fixed_grams must be >= 0: K test"):
        solve_recipe_data(recipe, ferts=ferts, mm=molar_masses)


def test_solve_recipe_data_rejects_fixed_grams_outside_allowed_list() -> None:
    molar_masses = load_molar_masses()
    ferts = {
        "K test": Fertilizer("K test", "fest", 1.0, {"K2O": 1.0}),
        "Other": Fertilizer("Other", "fest", 1.0, {"K2O": 1.0}),
    }
    recipe = {
        "liters": 1,
        "water_profile": {"mg_per_l": {}},
        "fertilizers_allowed": ["K test"],
        "fixed_grams": {"Other": 1.0},
        "targets": {"K": 100.0},
    }

    with pytest.raises(ValueError, match="fixed_grams not in fertilizers_allowed"):
        solve_recipe_data(recipe, ferts=ferts, mm=molar_masses)


def test_solve_recipe_data_does_not_use_water_elements_as_targets() -> None:
    molar_masses = load_molar_masses()
    ferts = {
        "K test": Fertilizer("K test", "fest", 1.0, {"K2O": 1.0}),
    }
    recipe = {
        "liters": 1,
        "water_profile": {"mg_per_l": {}},
        "fertilizers_allowed": ["K test"],
        "water_elements_mg_per_l": {"K": 100.0},
    }

    with pytest.raises(ValueError, match="No solvable targets defined"):
        solve_recipe_data(recipe, ferts=ferts, mm=molar_masses)


def test_solve_recipe_data_can_solve_hco3_from_direct_hco3_composition() -> None:
    molar_masses = load_molar_masses()
    ferts = {
        "HCO3 test": Fertilizer("HCO3 test", "fest", 1.0, {"HCO3": 1.0}),
    }
    recipe = {
        "liters": 1,
        "water_profile": {"mg_per_l": {}},
        "fertilizers_allowed": ["HCO3 test"],
        "targets": {"HCO3": 100.0},
    }

    result = solve_recipe_data(recipe, ferts=ferts, mm=molar_masses)

    assert result.objective_elements == ["HCO3"]
    assert result.fertilizers[0]["name"] == "HCO3 test"
    assert result.fertilizers[0]["grams"] > 0
