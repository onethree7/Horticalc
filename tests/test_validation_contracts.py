from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from horticalc.core import compute_solution
from horticalc.data_io import Fertilizer, load_fertilizers, load_molar_masses
from horticalc.solver import solve_recipe_data
from horticalc.solver_config import validate_solver_config

ROOT = Path(__file__).resolve().parents[1]


def test_calculator_defaults_only_omitted_or_null_liters() -> None:
    fertilizers = load_fertilizers()
    molar_masses = load_molar_masses()

    assert compute_solution({}, fertilizers, molar_masses).liters == 10.0
    assert compute_solution({"liters": None}, fertilizers, molar_masses).liters == 10.0
    for value in (0, -1, float("nan"), float("inf")):
        with pytest.raises(ValueError, match="liters"):
            compute_solution({"liters": value}, fertilizers, molar_masses)


@pytest.mark.parametrize("grams", [-1, float("nan"), float("inf")])
def test_calculator_rejects_invalid_fertilizer_amounts(grams: float) -> None:
    recipe = {"fertilizers": [{"name": "unused", "grams": grams}]}
    with pytest.raises(ValueError, match="grams"):
        compute_solution(recipe, {}, load_molar_masses())


@pytest.mark.parametrize("osmosis", [-0.1, 100.1, float("nan"), float("inf")])
def test_calculator_rejects_invalid_water_contracts(osmosis: float) -> None:
    with pytest.raises(ValueError, match="osmosis_percent"):
        compute_solution({}, {}, load_molar_masses(), {}, osmosis_percent=osmosis)

    with pytest.raises(ValueError, match="water_mg_l.Ca"):
        compute_solution({}, {}, load_molar_masses(), {"Ca": -1})


@pytest.mark.parametrize(
    "config",
    [
        {"overshoot_penalty": -0.1},
        {"irls_max_outer_iter": 0},
        {"irls_max_outer_iter": 13},
        {"scale_eps_mg_per_l": 0},
        {"singleton_share_threshold": -0.1},
        {"singleton_share_threshold": 1.1},
        {"singleton_max_regress_pp": -0.1},
        {"singleton_underfill_share_threshold": -0.1},
        {"singleton_underfill_share_threshold": 1.1},
        {"singleton_underfill_max_iter": 0},
        {"singleton_underfill_max_iter": 9},
        {"n_total_governor_weight": -0.1},
    ],
)
def test_solver_schema_enforces_every_numeric_bound(config: dict) -> None:
    with pytest.raises(ValueError, match="Invalid solver config value"):
        validate_solver_config(config)


def test_one_irls_iteration_performs_the_initial_solve() -> None:
    fertilizer = Fertilizer("K test", False, 1.0, {"K2O": 1.0})
    result = solve_recipe_data(
        {
            "liters": 1,
            "water_profile": {"mg_per_l": {}},
            "fertilizers_allowed": [fertilizer.name],
            "targets": {"K": 100},
            "solver_config": {"relative_weighting": True, "irls_max_outer_iter": 1},
        },
        ferts={fertilizer.name: fertilizer},
        mm=load_molar_masses(),
    )

    assert result.fertilizers
    assert result.achieved_elements_mg_l["K"] == pytest.approx(100)


def test_empty_injected_fertilizer_mapping_is_not_replaced(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("horticalc.solver.load_fertilizers", lambda: pytest.fail("unexpected load"))
    with pytest.raises(KeyError, match="Unknown fertilizer"):
        solve_recipe_data(
            {
                "targets": {"K": 1},
                "fertilizers_allowed": ["missing"],
                "water_profile": {"mg_per_l": {}},
            },
            ferts={},
            mm=load_molar_masses(),
        )


def test_cli_domain_errors_exit_with_code_two(tmp_path: Path) -> None:
    recipe = tmp_path / "invalid.yml"
    recipe.write_text("liters: 0\nfertilizers: []\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "-m", "horticalc", str(recipe)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 2
    assert "liters" in result.stderr
