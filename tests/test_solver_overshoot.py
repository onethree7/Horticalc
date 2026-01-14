import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from horticalc.data_io import load_fertilizers, load_molar_masses
from horticalc.solver import solve_recipe_data


def test_fixed_grams_zero_not_fixed() -> None:
    ferts = load_fertilizers()
    mm = load_molar_masses()
    recipe = {
        "liters": 10,
        "targets": {"K": 50},
        "fertilizers_allowed": ["S3 Kaliwasser 28 Be"],
        "fixed_grams": {"S3 Kaliwasser 28 Be": 0},
    }
    result = solve_recipe_data(recipe, ferts=ferts, mm=mm)
    assert result.fertilizers, "Expected solver to treat 0g fixed values as variable."
    assert result.fertilizers[0]["grams"] > 0


def test_overshoot_penalty_reduces_si() -> None:
    ferts = load_fertilizers()
    mm = load_molar_masses()
    recipe_base = {
        "liters": 10,
        "targets": {"K": 200, "Si": 1, "Ca": 120},
        "fertilizers_allowed": ["S3 Kaliwasser 28 Be", "Yara Tera CALCINIT"],
    }
    result_no_penalty = solve_recipe_data(
        {**recipe_base, "overshoot": {"enabled": False}},
        ferts=ferts,
        mm=mm,
    )
    result_with_penalty = solve_recipe_data(
        {
            **recipe_base,
            "overshoot": {
                "enabled": True,
                "max_iters": 4,
                "weight_step": 4.0,
                "max_weight": 50.0,
            },
        },
        ferts=ferts,
        mm=mm,
    )
    si_no_penalty = result_no_penalty.achieved_elements_mg_l.get("Si", 0.0)
    si_with_penalty = result_with_penalty.achieved_elements_mg_l.get("Si", 0.0)
    assert si_with_penalty < si_no_penalty
