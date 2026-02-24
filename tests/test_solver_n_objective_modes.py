import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from horticalc.data_io import Fertilizer, load_molar_masses
from horticalc.solver import _filter_n_objective_keys, _objective_keys, solve_recipe_data


def test_filter_n_objective_keys_modes() -> None:
    keys = ["N_total", "N_NO3", "N_NH4", "N_UREA", "P", "K"]

    assert _filter_n_objective_keys(keys, "total_only") == ["N_total", "P", "K"]
    assert _filter_n_objective_keys(keys, "forms_only") == ["N_NO3", "N_NH4", "N_UREA", "P", "K"]
    assert _filter_n_objective_keys(keys, "combined") == keys


def test_default_mode_is_total_only() -> None:
    molar_masses = load_molar_masses()
    ferts = {
        "NO3-only": Fertilizer(name="NO3-only", form="solid", weight_factor=1.0, comp={"NO3": 1.0}),
        "NH4-only": Fertilizer(name="NH4-only", form="solid", weight_factor=1.0, comp={"NH4": 1.0}),
    }
    recipe = {
        "liters": 1.0,
        "targets": {"N_total": 100.0, "N_NO3": 70.0, "N_NH4": 30.0},
        "fertilizers_allowed": ["NO3-only", "NH4-only"],
    }

    result_default = solve_recipe_data(recipe, ferts=ferts, mm=molar_masses)
    assert result_default.objective_elements == ["N_total"]

    recipe_explicit = dict(recipe)
    recipe_explicit["solver_config"] = {"n_objective_mode": "total_only"}
    result_explicit = solve_recipe_data(recipe_explicit, ferts=ferts, mm=molar_masses)

    assert result_default.fertilizers == result_explicit.fertilizers
    assert result_default.objective_elements == result_explicit.objective_elements


def test_objective_modes_applied_in_solver() -> None:
    targets = {"N_total": 100.0, "N_NO3": 70.0, "N_NH4": 30.0, "P": 10.0}
    keys = _objective_keys(targets)

    assert _filter_n_objective_keys(keys, "total_only") == ["N_total", "P"]
    assert _filter_n_objective_keys(keys, "forms_only") == ["N_NO3", "N_NH4", "P"]
    assert _filter_n_objective_keys(keys, "combined") == ["N_total", "N_NO3", "N_NH4", "P"]
