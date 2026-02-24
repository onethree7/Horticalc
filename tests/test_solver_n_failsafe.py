import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from horticalc.data_io import Fertilizer, load_molar_masses
from horticalc.solver import solve_recipe_data


def test_n_failsafe_switches_to_total_only_when_macros_blow_up() -> None:
    ferts = {
        "NO3-P": Fertilizer(name="NO3-P", form="solid", weight_factor=1.0, comp={"NO3": 1.0, "P2O5": 1.0}),
        "NH4-only": Fertilizer(name="NH4-only", form="solid", weight_factor=1.0, comp={"NH4": 1.0}),
        "K-only": Fertilizer(name="K-only", form="solid", weight_factor=1.0, comp={"K2O": 1.0}),
        "Ca-only": Fertilizer(name="Ca-only", form="solid", weight_factor=1.0, comp={"CaO": 1.0}),
        "Mg-only": Fertilizer(name="Mg-only", form="solid", weight_factor=1.0, comp={"MgO": 1.0}),
    }
    recipe = {
        "liters": 1.0,
        "targets": {
            "N_total": 120.0,
            "N_NO3": 110.0,
            "N_NH4": 10.0,
            "P": 10.0,
            "K": 60.0,
            "Ca": 40.0,
            "Mg": 20.0,
        },
        "fertilizers_allowed": ["NO3-P", "NH4-only", "K-only", "Ca-only", "Mg-only"],
        "solver_config": {
            "n_objective_mode": "combined",
            "n_failsafe_enabled": True,
            "n_failsafe_macro_error_cap_pp": 10.0,
        },
    }

    result = solve_recipe_data(recipe, ferts=ferts, mm=load_molar_masses())

    assert result.diagnostics["n_failsafe_triggered"] is True
    assert result.objective_elements == ["N_total", "P", "K", "Ca", "Mg"]
