import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from horticalc.solver import solve_recipe


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

    for key in result.objective_elements:
        target = targets.get(key, 0.0)
        actual = achieved.get(key, 0.0)
        if target == 0.0:
            continue
        abs_tol = 3.0 if target >= 1.0 else 0.2
        rel_tol = 0.07
        assert abs(actual - target) <= max(abs_tol, rel_tol * target), f"{key} off: {actual} vs {target}"
