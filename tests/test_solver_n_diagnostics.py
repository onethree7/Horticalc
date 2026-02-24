import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from horticalc.data_io import Fertilizer, load_molar_masses
from horticalc.solver import solve_recipe_data


def test_n_diagnostics_flags_conflict_for_incompatible_split() -> None:
    ferts = {
        "NO3-P": Fertilizer(name="NO3-P", form="solid", weight_factor=1.0, comp={"NO3": 1.0, "P2O5": 0.8}),
    }
    recipe = {
        "liters": 1.0,
        "targets": {"N_total": 100.0, "N_NO3": 50.0, "N_NH4": 50.0, "P": 5.0},
        "fertilizers_allowed": ["NO3-P"],
        "solver_config": {"n_objective_mode": "combined", "relative_weighting": True, "n_failsafe_enabled": False},
    }

    result = solve_recipe_data(recipe, ferts=ferts, mm=load_molar_masses())

    assert result.diagnostics["n_split_conflict"] is True
    assert result.diagnostics["n_form_infeasible_with_basis"] is True
    assert result.diagnostics["co_delivery_pressure_P"] is True
    assert "NO3-P" in result.diagnostics["dominant_n_fertilizers"]


def test_n_diagnostics_no_conflict_for_compatible_split() -> None:
    ferts = {
        "NO3-only": Fertilizer(name="NO3-only", form="solid", weight_factor=1.0, comp={"NO3": 1.0}),
        "NH4-only": Fertilizer(name="NH4-only", form="solid", weight_factor=1.0, comp={"NH4": 1.0}),
    }
    recipe = {
        "liters": 1.0,
        "targets": {"N_total": 100.0, "N_NO3": 60.0, "N_NH4": 40.0},
        "fertilizers_allowed": ["NO3-only", "NH4-only"],
        "solver_config": {"n_objective_mode": "combined", "relative_weighting": True, "n_failsafe_enabled": False},
    }

    result = solve_recipe_data(recipe, ferts=ferts, mm=load_molar_masses())

    assert result.diagnostics["n_split_conflict"] is False
    assert result.diagnostics["n_form_infeasible_with_basis"] is False
    assert result.diagnostics["co_delivery_pressure_P"] is False
    assert result.diagnostics["co_delivery_pressure_Ca"] is False
