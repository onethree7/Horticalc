import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from horticalc.data_io import Fertilizer, load_molar_masses
from horticalc.solver import solve_recipe_data


def test_n_failsafe_prefers_macro_stability() -> None:
    molar_masses = load_molar_masses()
    ferts = {
        "NO3+P": Fertilizer(name="NO3+P", form="solid", weight_factor=1.0, comp={"NO3": 1.0, "P2O5": 1.0}),
        "NH4-only": Fertilizer(name="NH4-only", form="solid", weight_factor=1.0, comp={"NH4": 1.0}),
    }
    targets = {"N_total": 100.0, "N_NO3": 90.0, "N_NH4": 10.0, "P": 2.0}

    combined_recipe = {
        "liters": 1.0,
        "targets": targets,
        "fertilizers_allowed": ["NO3+P", "NH4-only"],
        "solver_config": {
            "n_objective_mode": "combined",
            "n_failsafe_enabled": False,
            "stage_optimization_enabled": False,
        },
    }
    combined_result = solve_recipe_data(combined_recipe, ferts=ferts, mm=molar_masses)
    combined_p_error = abs(combined_result.errors_percent.get("P", 0.0))

    guarded_recipe = {
        "liters": 1.0,
        "targets": targets,
        "fertilizers_allowed": ["NO3+P", "NH4-only"],
        "solver_config": {
            "n_objective_mode": "combined",
            "n_failsafe_enabled": True,
            "n_failsafe_macro_error_cap_pp": 10.0,
            "stage_optimization_enabled": False,
        },
    }
    guarded_result = solve_recipe_data(guarded_recipe, ferts=ferts, mm=molar_masses)

    assert guarded_result.diagnostics["n_failsafe_triggered"] is True
    assert "N_total" in guarded_result.objective_elements
    assert "N_NO3" not in guarded_result.objective_elements
    assert abs(guarded_result.errors_percent.get("P", 0.0)) < combined_p_error
