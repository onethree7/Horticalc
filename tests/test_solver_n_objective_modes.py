import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from horticalc.data_io import Fertilizer, load_molar_masses
from horticalc.solver import solve_recipe_data


def _ferts() -> dict[str, Fertilizer]:
    return {
        "NO3-only": Fertilizer(name="NO3-only", form="solid", weight_factor=1.0, comp={"NO3": 1.0}),
        "NH4-only": Fertilizer(name="NH4-only", form="solid", weight_factor=1.0, comp={"NH4": 1.0}),
    }


def test_n_objective_mode_total_only_selects_total() -> None:
    recipe = {
        "liters": 1.0,
        "targets": {"N_total": 10.0, "N_NO3": 7.0, "N_NH4": 3.0},
        "fertilizers_allowed": ["NO3-only", "NH4-only"],
    }
    result = solve_recipe_data(recipe, ferts=_ferts(), mm=load_molar_masses())

    assert result.objective_elements == ["N_total"]


def test_n_objective_mode_forms_only_drops_total() -> None:
    recipe = {
        "liters": 1.0,
        "targets": {"N_total": 10.0, "N_NO3": 7.0, "N_NH4": 3.0},
        "fertilizers_allowed": ["NO3-only", "NH4-only"],
        "solver_config": {"n_objective_mode": "forms_only"},
    }
    result = solve_recipe_data(recipe, ferts=_ferts(), mm=load_molar_masses())

    assert "N_total" not in result.objective_elements
    assert "N_NO3" in result.objective_elements
    assert "N_NH4" in result.objective_elements


def test_n_objective_mode_combined_keeps_all() -> None:
    recipe = {
        "liters": 1.0,
        "targets": {"N_total": 10.0, "N_NO3": 7.0, "N_NH4": 3.0},
        "fertilizers_allowed": ["NO3-only", "NH4-only"],
        "solver_config": {"n_objective_mode": "combined"},
    }
    result = solve_recipe_data(recipe, ferts=_ferts(), mm=load_molar_masses())

    assert "N_total" in result.objective_elements
    assert "N_NO3" in result.objective_elements
    assert "N_NH4" in result.objective_elements
