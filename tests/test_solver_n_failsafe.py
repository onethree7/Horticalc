import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from horticalc.data_io import Fertilizer, load_molar_masses
from horticalc.solver import solve_recipe_data


def test_n_failsafe_switches_to_total_only_when_macros_destabilize() -> None:
    mm = load_molar_masses()
    ferts = {
        "NO3+P+Ca": Fertilizer(
            name="NO3+P+Ca",
            form="solid",
            weight_factor=1.0,
            comp={"NO3": 1.0, "P2O5": 1.0, "CaO": 1.0},
        ),
        "NH4-only": Fertilizer(name="NH4-only", form="solid", weight_factor=1.0, comp={"NH4": 1.0}),
    }
    recipe = {
        "liters": 1.0,
        "targets": {"N_total": 100.0, "N_NO3": 80.0, "N_NH4": 20.0, "P": 1.0, "Ca": 1.0},
        "fertilizers_allowed": ["NO3+P+Ca", "NH4-only"],
        "solver_config": {
            "n_objective_mode": "combined",
            "n_failsafe_enabled": True,
            "n_failsafe_macro_error_cap_pp": 25.0,
        },
    }

    combined_no_failsafe = solve_recipe_data(
        {**recipe, "solver_config": {**recipe["solver_config"], "n_failsafe_enabled": False}},
        ferts=ferts,
        mm=mm,
    )
    with_failsafe = solve_recipe_data(recipe, ferts=ferts, mm=mm)

    def macro_max_error(result) -> float:
        vals = []
        for key in ("P", "Ca"):
            target = result.targets_mg_l[key]
            achieved = result.achieved_elements_mg_l.get(key, 0.0)
            vals.append(abs((achieved - target) / target * 100.0))
        return max(vals)

    assert with_failsafe.diagnostics["n_failsafe_triggered"] is True
    assert macro_max_error(with_failsafe) < macro_max_error(combined_no_failsafe)
