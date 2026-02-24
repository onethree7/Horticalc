import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from horticalc.data_io import Fertilizer, load_molar_masses
from horticalc.solver import solve_recipe_data


def test_n_diagnostics_flags_incompatible_split() -> None:
    molar_masses = load_molar_masses()
    ferts = {
        "N-P": Fertilizer(name="N-P", form="solid", weight_factor=1.0, comp={"NO3": 1.0, "P2O5": 1.0}),
    }
    recipe = {
        "liters": 1.0,
        "targets": {"N_total": 100.0, "N_NO3": 50.0, "N_NH4": 50.0},
        "fertilizers_allowed": ["N-P"],
        "solver_config": {
            "n_objective_mode": "combined",
            "n_diag_total_match_tol_pp": 5.0,
            "n_diag_form_error_tol_pp": 20.0,
            "n_diag_basis_infeasible_tol_pp": 5.0,
        },
    }

    result = solve_recipe_data(recipe, ferts=ferts, mm=molar_masses)
    diagnostics = result.diagnostics

    assert diagnostics["n_split_conflict"] is True
    assert diagnostics["n_form_infeasible_with_basis"] is True
    assert diagnostics["dominant_n_fertilizers"] == ["N-P"]


def test_n_diagnostics_detects_p_co_delivery_pressure() -> None:
    molar_masses = load_molar_masses()
    ferts = {
        "N-P": Fertilizer(name="N-P", form="solid", weight_factor=1.0, comp={"NO3": 1.0, "P2O5": 1.0}),
    }
    recipe = {
        "liters": 1.0,
        "targets": {"N_total": 100.0, "P": 5.0},
        "fertilizers_allowed": ["N-P"],
        "solver_config": {
            "n_objective_mode": "total_only",
            "n_diag_macro_pressure_tol_pp": 20.0,
        },
    }

    result = solve_recipe_data(recipe, ferts=ferts, mm=molar_masses)
    diagnostics = result.diagnostics

    assert diagnostics["co_delivery_pressure_P"] is True


def test_n_diagnostics_clear_for_compatible_split() -> None:
    molar_masses = load_molar_masses()
    ferts = {
        "NO3-only": Fertilizer(name="NO3-only", form="solid", weight_factor=1.0, comp={"NO3": 1.0}),
        "NH4-only": Fertilizer(name="NH4-only", form="solid", weight_factor=1.0, comp={"NH4": 1.0}),
    }
    recipe = {
        "liters": 1.0,
        "targets": {"N_total": 100.0, "N_NO3": 50.0, "N_NH4": 50.0},
        "fertilizers_allowed": ["NO3-only", "NH4-only"],
        "solver_config": {
            "n_objective_mode": "combined",
            "n_diag_total_match_tol_pp": 2.0,
            "n_diag_form_error_tol_pp": 10.0,
            "n_diag_basis_infeasible_tol_pp": 10.0,
        },
    }

    result = solve_recipe_data(recipe, ferts=ferts, mm=molar_masses)
    diagnostics = result.diagnostics

    assert diagnostics["n_split_conflict"] is False
    assert diagnostics["n_form_infeasible_with_basis"] is False
