import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from horticalc.data_io import Fertilizer, load_molar_masses
from horticalc.solver import solve_recipe_data


def _ferts() -> dict[str, Fertilizer]:
    return {
        "N-only": Fertilizer(name="N-only", form="solid", weight_factor=1.0, comp={"NO3": 1.0}),
    }


def _recipe(mode: str | None) -> dict:
    solver_config = {"relative_weighting": True}
    if mode is not None:
        solver_config["n_objective_mode"] = mode
    return {
        "liters": 1.0,
        "targets": {"N_total": 100.0, "N_NO3": 60.0, "N_NH4": 40.0},
        "fertilizers_allowed": ["N-only"],
        "solver_config": solver_config,
    }


def test_n_objective_mode_total_only_uses_only_n_total() -> None:
    result = solve_recipe_data(_recipe("total_only"), ferts=_ferts(), mm=load_molar_masses())
    assert "N_total" in result.objective_elements
    assert "N_NO3" not in result.objective_elements
    assert "N_NH4" not in result.objective_elements


def test_n_objective_mode_forms_only_drops_n_total() -> None:
    result = solve_recipe_data(_recipe("forms_only"), ferts=_ferts(), mm=load_molar_masses())
    assert "N_total" not in result.objective_elements
    assert "N_NO3" in result.objective_elements
    assert "N_NH4" in result.objective_elements


def test_n_objective_mode_combined_keeps_total_and_forms() -> None:
    result = solve_recipe_data(_recipe("combined"), ferts=_ferts(), mm=load_molar_masses())
    assert "N_total" in result.objective_elements
    assert "N_NO3" in result.objective_elements
    assert "N_NH4" in result.objective_elements


def test_default_n_objective_mode_matches_total_only() -> None:
    default_result = solve_recipe_data(_recipe(None), ferts=_ferts(), mm=load_molar_masses())
    explicit_total = solve_recipe_data(_recipe("total_only"), ferts=_ferts(), mm=load_molar_masses())
    assert default_result.objective_elements == explicit_total.objective_elements
