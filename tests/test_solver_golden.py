from pathlib import Path

from horticalc.solver import solve_recipe

def _percent_error(actual: float, target: float) -> float:
    if target == 0.0:
        return abs(actual)
    return abs(actual - target) / abs(target) * 100.0

def test_solver_golden_solution_close() -> None:
    recipe_path = Path(__file__).resolve().parents[1] / "recipes" / "solve_golden.yml"
    result = solve_recipe(recipe_path)

    objective_upper = {key.upper() for key in result.objective_elements}
    assert "S" not in objective_upper
    assert "SO4" not in objective_upper
    assert "NA" not in objective_upper
    assert "CL" not in objective_upper

    targets = result.targets_mg_l
    achieved = result.achieved_elements_mg_l

    percent_errors = {}
    for key in result.objective_elements:
        target = targets.get(key, 0.0)
        actual = achieved.get(key, 0.0)
        if target == 0.0:
            continue
        percent_errors[key] = _percent_error(actual, target)

    macro_keys = {"N_TOTAL", "N_NH4", "N_NO3", "N_UREA", "P", "K", "CA", "MG"}
    macro_errors = {key: error for key, error in percent_errors.items() if key.upper() in macro_keys}
    micro_errors = {key: error for key, error in percent_errors.items() if key.upper() not in macro_keys}
    rms_percent_error = (sum(error * error for error in percent_errors.values()) / len(percent_errors)) ** 0.5

    assert max(macro_errors.values()) <= 15.0
    assert max(micro_errors.values()) <= 5.0
    assert rms_percent_error <= 8.0
