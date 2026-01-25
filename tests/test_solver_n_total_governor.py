import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from horticalc.solver import solve_recipe


def test_n_total_governor_prioritizes_no3_target() -> None:
    recipe_path = Path(__file__).resolve().parents[1] / "recipes" / "solve_n_total_governor.yml"
    result = solve_recipe(recipe_path)

    targets = result.targets_mg_l
    achieved = result.achieved_elements_mg_l

    no3_target = targets["N_NO3"]
    assert achieved["N_NO3"] >= no3_target * 0.95
    assert achieved["N_total"] >= achieved["N_NO3"]
    assert achieved["N_total"] > targets["N_total"]
