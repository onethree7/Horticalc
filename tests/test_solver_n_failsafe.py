import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from horticalc.data_io import Fertilizer, load_molar_masses
from horticalc.solver import solve_recipe_data


def test_n_failsafe_switches_from_combined_to_total_only() -> None:
    ferts = {
        "N-clean": Fertilizer(name="N-clean", form="solid", weight_factor=1.0, comp={"NO3": 1.0}),
        "NH4-Ca": Fertilizer(name="NH4-Ca", form="solid", weight_factor=1.0, comp={"NH4": 1.0, "CaO": 1.2}),
    }
    base_recipe = {
        "liters": 1.0,
        "targets": {"N_total": 100.0, "N_NO3": 90.0, "N_NH4": 10.0, "Ca": 1.0},
        "fertilizers_allowed": ["N-clean", "NH4-Ca"],
    }

    combined_no_failsafe = {
        **base_recipe,
        "solver_config": {
            "n_objective_mode": "combined",
            "n_failsafe_enabled": False,
            "relative_weighting": True,
        },
    }
    combined_with_failsafe = {
        **base_recipe,
        "solver_config": {
            "n_objective_mode": "combined",
            "n_failsafe_enabled": True,
            "n_failsafe_macro_error_cap_pp": 5.0,
            "relative_weighting": True,
        },
    }

    no_failsafe_result = solve_recipe_data(combined_no_failsafe, ferts=ferts, mm=load_molar_masses())
    with_failsafe_result = solve_recipe_data(combined_with_failsafe, ferts=ferts, mm=load_molar_masses())

    ca_no_failsafe = abs(no_failsafe_result.errors_percent.get("Ca", 0.0))
    ca_with_failsafe = abs(with_failsafe_result.errors_percent.get("Ca", 0.0))

    assert with_failsafe_result.diagnostics["n_failsafe_triggered"] is True
    assert ca_with_failsafe < ca_no_failsafe
    assert with_failsafe_result.objective_elements == ["N_total", "Ca"]
