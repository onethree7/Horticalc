import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from horticalc.data_io import Fertilizer, load_molar_masses
from horticalc.solver import solve_recipe_data


def test_n_diagnostics_flags_incompatible_split() -> None:
    result = solve_recipe_data(
        {
            "liters": 1.0,
            "targets": {"N_total": 100.0, "N_NO3": 50.0, "N_NH4": 50.0, "P": 1.0, "Ca": 1.0},
            "fertilizers_allowed": ["NO3+P+Ca"],
            "solver_config": {
                "n_objective_mode": "combined",
                "n_diag_form_residual_tol_pp": 5.0,
                "n_diag_total_residual_tol_pp": 5.0,
                "n_diag_macro_pressure_threshold_pp": 10.0,
            },
        },
        ferts={
            "NO3+P+Ca": Fertilizer(
                name="NO3+P+Ca",
                form="solid",
                weight_factor=1.0,
                comp={"NO3": 1.0, "P2O5": 1.0, "CaO": 1.0},
            )
        },
        mm=load_molar_masses(),
    )
    d = result.diagnostics
    assert d["n_split_conflict"] is True
    assert d["n_form_infeasible_with_basis"] is True
    assert d["co_delivery_pressure_P"] is True
    assert d["co_delivery_pressure_Ca"] is True
    assert d["dominant_n_fertilizers"] == ["NO3+P+Ca"]


def test_n_diagnostics_clear_for_compatible_split() -> None:
    result = solve_recipe_data(
        {
            "liters": 1.0,
            "targets": {"N_total": 100.0, "N_NO3": 70.0, "N_NH4": 30.0},
            "fertilizers_allowed": ["NO3-only", "NH4-only"],
            "solver_config": {
                "n_objective_mode": "combined",
                "n_diag_form_residual_tol_pp": 5.0,
                "n_diag_total_residual_tol_pp": 5.0,
            },
        },
        ferts={
            "NO3-only": Fertilizer(name="NO3-only", form="solid", weight_factor=1.0, comp={"NO3": 1.0}),
            "NH4-only": Fertilizer(name="NH4-only", form="solid", weight_factor=1.0, comp={"NH4": 1.0}),
        },
        mm=load_molar_masses(),
    )
    d = result.diagnostics
    assert d["n_split_conflict"] is False
    assert d["n_form_infeasible_with_basis"] is False
