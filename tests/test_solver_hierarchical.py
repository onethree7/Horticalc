from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import yaml

from horticalc.data_io import (
    Fertilizer,
    load_fertilizers,
    load_molar_masses,
    load_nutrient_solution_data,
    load_water_profile_data,
)
from horticalc.paths import shipped_fertilizers_path
from horticalc.priority_solver import solve_hierarchical_priorities
from horticalc.solver import solve_recipe_data

ROOT = Path(__file__).resolve().parents[1]
MOLAR_MASSES = load_molar_masses()


def _fertilizer(name: str, comp: dict[str, float], *, maximum: float | None = None) -> Fertilizer:
    return Fertilizer(
        name=name,
        liquid=False,
        weight_factor=1.0,
        comp=comp,
        solver_max_dose_per_l=maximum,
    )


def test_higher_priority_cannot_be_traded_for_any_lower_priority_improvement() -> None:
    result = solve_hierarchical_priorities(
        np.array([[1.0], [1.0]]),
        np.array([10.0, 100.0]),
        np.array([np.inf]),
        [(1, 1), (2, 2)],
        np.array([1.0]),
    )

    assert result.doses == pytest.approx([10.0], abs=1e-6)
    assert result.stages[0].priority == 1
    assert result.stages[0].max_error_mg_per_l == pytest.approx(0.0, abs=1e-6)
    assert result.stages[1].priority == 2
    assert result.stages[1].max_error_mg_per_l == pytest.approx(90.0, abs=1e-6)


def test_directional_priorities_treat_underfill_and_overshoot_independently() -> None:
    result = solve_hierarchical_priorities(
        np.array([[1.0], [1.0]]),
        np.array([10.0, 5.0]),
        np.array([np.inf]),
        [(1, 4), (4, 1)],
        np.array([1.0]),
    )

    assert result.doses == pytest.approx([7.5], abs=1e-5)
    assert result.stages[0].priority == 1
    assert result.stages[0].max_error_mg_per_l == pytest.approx(2.5, abs=1e-6)
    assert result.stages[0].total_error_mg_per_l == pytest.approx(5.0, abs=1e-5)


def test_hierarchical_solver_reports_zero_priority_targets_without_optimizing_them() -> None:
    result = solve_recipe_data(
        {
            "liters": 10.0,
            "targets_mg_per_l": {"N_total": 100.0, "Cu": 0.1},
            "fertilizers_allowed": ["Coupled"],
            "solver_config": {
                "solver_model": "hierarchical",
                "target_priorities": {
                    "N_total": {"under": 1, "over": 1},
                    "Cu": {"under": 0, "over": 0},
                },
            },
        },
        ferts={"Coupled": _fertilizer("Coupled", {"NO3": 0.1, "Cu": 0.01})},
        mm=MOLAR_MASSES,
        water_profile_data={"mg_per_l": {}},
    )

    assert result.solver_model == "hierarchical"
    assert result.objective_elements == ["N_total"]
    assert result.ignored_elements == ["Cu"]
    assert result.target_priorities == {
        "N_total": {"under": 1, "over": 1},
        "Cu": {"under": 0, "over": 0},
    }
    assert result.errors_mg_l["N_total"] == pytest.approx(0.0, abs=1e-5)
    assert "Cu" not in result.errors_mg_l
    assert result.achieved_elements_mg_l["Cu"] == pytest.approx(10.0, abs=1e-5)
    assert result.priority_stages[0]["priority"] == 1


def test_hierarchical_solver_honors_fixed_doses_and_product_maximums() -> None:
    result = solve_recipe_data(
        {
            "liters": 10.0,
            "targets_mg_per_l": {"N_total": 100.0},
            "fertilizers_allowed": ["Fixed", "Limited"],
            "fixed_grams": {"Fixed": 2.0},
            "solver_config": {
                "solver_model": "hierarchical",
                "target_priorities": {"N_total": {"under": 1, "over": 1}},
            },
        },
        ferts={
            "Fixed": _fertilizer("Fixed", {"NO3": 0.1}),
            "Limited": _fertilizer("Limited", {"NO3": 0.1}, maximum=0.5),
        },
        mm=MOLAR_MASSES,
        water_profile_data={"mg_per_l": {}},
    )

    doses = {row["name"]: float(row["grams"]) for row in result.fertilizers}
    assert doses == pytest.approx({"Fixed": 2.0, "Limited": 5.0}, abs=1e-6)
    assert result.achieved_elements_mg_l["N_total"] == pytest.approx(70.0, abs=1e-5)
    assert result.priority_stages[0]["max_error_mg_per_l"] == pytest.approx(30.0, abs=1e-5)


def test_hierarchical_solver_rejects_report_only_configuration_for_every_target() -> None:
    with pytest.raises(ValueError, match="all active targets are ignored"):
        solve_recipe_data(
            {
                "targets_mg_per_l": {"N_total": 100.0},
                "fertilizers_allowed": ["N"],
                "solver_config": {
                    "solver_model": "hierarchical",
                    "target_priorities": {"N_total": {"under": 0, "over": 0}},
                },
            },
            ferts={"N": _fertilizer("N", {"NO3": 0.1})},
            mm=MOLAR_MASSES,
            water_profile_data={"mg_per_l": {}},
        )


@pytest.mark.parametrize(
    "profile_name",
    [
        "Saloner_Bernstein_Cannabis_NPK_Target_Optimization.yml",
        "Bugbee_Utah_Hydroponic_Cannabis_2022.yml",
    ],
)
def test_configured_priorities_protect_npk_and_iron_in_real_profiles(profile_name: str) -> None:
    recipe = yaml.safe_load((ROOT / "recipes" / "solve_augmented_saloner_bernstein.yml").read_text(encoding="utf-8"))
    profile = load_nutrient_solution_data(ROOT / "data" / "nutrient_solutions" / profile_name)
    priorities = {key: {"under": 1, "over": 1} for key in ("N_total", "P", "K")}
    priorities.update(
        {
            "Fe": {"under": 2, "over": 2},
            "Ca": {"under": 2, "over": 3},
            "Mg": {"under": 2, "over": 3},
            "S": {"under": 2, "over": 3},
        }
    )
    priorities.update({key: {"under": 4, "over": 4} for key in ("Mn", "Cu", "Zn", "B", "Mo")})
    recipe["targets_mg_per_l"] = profile["targets_mg_per_l"]
    recipe["solver_config"] = {
        "solver_model": "hierarchical",
        "target_priorities": priorities,
    }

    result = solve_recipe_data(
        recipe,
        ferts=load_fertilizers(shipped_fertilizers_path(ROOT)),
        mm=MOLAR_MASSES,
        water_profile_data=load_water_profile_data(ROOT / "data" / "water_profiles" / "65936.yml"),
    )

    for key in ("N_total", "P", "K", "Fe"):
        assert abs(result.errors_mg_l[key]) < 2e-5
    assert result.achieved_elements_mg_l["Fe"] < 2.0
    assert all(float(row["grams"]) >= 0.0 for row in result.fertilizers)
