import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from horticalc.data_io import Fertilizer, load_molar_masses
from horticalc.solver import solve_recipe_data


def test_n_diagnostics_incompatible_split_flags_conflict() -> None:
    ferts = {
        "NH4-heavy": Fertilizer(
            name="NH4-heavy",
            form="solid",
            weight_factor=1.0,
            comp={"NH4": 1.0, "P2O5": 0.8, "CaO": 0.8},
        ),
    }
    recipe = {
        "liters": 1.0,
        "targets": {"N_NO3": 80.0, "N_NH4": 20.0, "P": 5.0, "Ca": 5.0},
        "fertilizers_allowed": ["NH4-heavy"],
        "solver_config": {"n_objective_mode": "combined", "n_macro_pressure_tolerance_pp": 20.0, "n_failsafe_enabled": False},
    }

    result = solve_recipe_data(recipe, ferts=ferts, mm=load_molar_masses())

    assert result.diagnostics["n_split_conflict"] is True
    assert result.diagnostics["n_form_infeasible_with_basis"] is True
    assert result.diagnostics["co_delivery_pressure_P"] is True
    assert result.diagnostics["co_delivery_pressure_Ca"] is True


def test_n_diagnostics_compatible_split_has_no_conflict() -> None:
    ferts = {
        "NO3-only": Fertilizer(name="NO3-only", form="solid", weight_factor=1.0, comp={"NO3": 1.0}),
        "NH4-only": Fertilizer(name="NH4-only", form="solid", weight_factor=1.0, comp={"NH4": 1.0}),
    }
    recipe = {
        "liters": 1.0,
        "targets": {"N_total": 100.0, "N_NO3": 80.0, "N_NH4": 20.0},
        "fertilizers_allowed": ["NO3-only", "NH4-only"],
        "solver_config": {"n_objective_mode": "combined", "n_failsafe_enabled": False},
    }

    result = solve_recipe_data(recipe, ferts=ferts, mm=load_molar_masses())

    assert result.diagnostics["n_split_conflict"] is False
    assert result.diagnostics["n_form_infeasible_with_basis"] is False
