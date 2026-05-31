import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from horticalc.data_io import Fertilizer, load_molar_masses
from horticalc.solver import solve_recipe, solve_recipe_data


def test_n_total_governor_prioritizes_n_total_target() -> None:
    recipe_path = Path(__file__).resolve().parents[1] / "recipes" / "solve_n_total_governor.yml"
    result = solve_recipe(recipe_path)

    targets = result.targets_mg_l
    achieved = result.achieved_elements_mg_l

    n_total_target = targets["N_total"]
    assert achieved["N_total"] <= n_total_target * 1.1
    assert achieved["N_total"] >= achieved["N_NO3"]


def test_objective_includes_n_total_with_forms() -> None:
    molar_masses = load_molar_masses()
    ferts = {
        "NO3-only": Fertilizer(name="NO3-only", form="solid", weight_factor=1.0, comp={"NO3": 1.0}),
    }
    recipe = {
        "liters": 1.0,
        "targets": {"N_total": 10.0, "N_NO3": 10.0},
        "fertilizers_allowed": ["NO3-only"],
        "solver_config": {"relative_weighting": True, "n_total_governor_enabled": False},
    }

    result = solve_recipe_data(recipe, ferts=ferts, mm=molar_masses)

    assert "N_total" in result.objective_elements


def test_nitrogen_objective_mode_n_total_only_excludes_forms() -> None:
    molar_masses = load_molar_masses()
    ferts = {
        "NO3-only": Fertilizer(name="NO3-only", form="solid", weight_factor=1.0, comp={"NO3": 1.0}),
    }
    recipe = {
        "liters": 1.0,
        "targets": {"N_total": 10.0, "N_NO3": 10.0, "N_NH4": 0.0, "N_UREA": 0.0},
        "fertilizers_allowed": ["NO3-only"],
        "solver_config": {"nitrogen_objective_mode": "n_total_only"},
    }

    result = solve_recipe_data(recipe, ferts=ferts, mm=molar_masses)

    assert "N_total" in result.objective_elements
    assert "N_NO3" not in result.objective_elements
    assert "N_NH4" not in result.objective_elements
    assert "N_UREA" not in result.objective_elements


def test_nitrogen_objective_mode_n_forms_only_excludes_total_and_keeps_zero_forms() -> None:
    molar_masses = load_molar_masses()
    ferts = {
        "NO3-only": Fertilizer(name="NO3-only", form="solid", weight_factor=1.0, comp={"NO3": 1.0}),
    }
    recipe = {
        "liters": 1.0,
        "targets": {"N_total": 10.0, "N_NO3": 10.0, "N_NH4": 0.0, "N_UREA": 0.0},
        "fertilizers_allowed": ["NO3-only"],
        "solver_config": {"nitrogen_objective_mode": "n_forms_only"},
    }

    result = solve_recipe_data(recipe, ferts=ferts, mm=molar_masses)

    assert "N_total" not in result.objective_elements
    assert "N_NO3" in result.objective_elements
    assert "N_NH4" in result.objective_elements
    assert "N_UREA" in result.objective_elements


def test_nitrogen_objective_mode_rejects_unknown_value() -> None:
    molar_masses = load_molar_masses()
    ferts = {
        "NO3-only": Fertilizer(name="NO3-only", form="solid", weight_factor=1.0, comp={"NO3": 1.0}),
    }
    recipe = {
        "liters": 1.0,
        "targets": {"N_total": 10.0},
        "fertilizers_allowed": ["NO3-only"],
        "solver_config": {"nitrogen_objective_mode": "chaos_mode"},
    }

    try:
        solve_recipe_data(recipe, ferts=ferts, mm=molar_masses)
    except ValueError as exc:
        assert "nitrogen_objective_mode" in str(exc)
    else:
        raise AssertionError("Expected invalid nitrogen_objective_mode to fail")
