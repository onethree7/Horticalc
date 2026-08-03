from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
import yaml

import scripts.solver_goal_model as goal
import scripts.solver_model_matrix as model_matrix
from horticalc.data_io import load_fertilizers, load_molar_masses, load_water_profile_data


def test_goal_lp_recovers_exact_nonnegative_solution() -> None:
    weights, stages = goal.solve_goal_weights(
        np.eye(2),
        np.array([2.0, 3.0]),
        np.array([np.inf, np.inf]),
        np.ones(2),
        "symmetric",
    )

    assert weights == pytest.approx([2.0, 3.0], abs=1e-8)
    assert stages["worst_absolute_error"] == pytest.approx(0.0, abs=1e-8)
    assert stages["total_absolute_error"] == pytest.approx(0.0, abs=1e-8)


def test_molar_goal_values_macro_error_more_than_same_mass_micro_error() -> None:
    matrix = np.array([[100.0], [0.4]])
    targets = np.array([100.0, 0.1])
    bounds = np.array([np.inf])
    mg_weights, _ = goal.solve_goal_weights(matrix, targets, bounds, np.ones(2), "symmetric")
    mmol_weights, _ = goal.solve_goal_weights(
        matrix,
        targets,
        bounds,
        np.array([1.0 / 14.0067, 1.0 / 63.546]),
        "symmetric",
    )

    mg_n_error = abs(float(matrix[0] @ mg_weights - targets[0]))
    mmol_n_error = abs(float(matrix[0] @ mmol_weights - targets[0]))
    assert mmol_n_error < mg_n_error


def test_global_underfill_factor_reduces_underfill_without_element_weights() -> None:
    matrix = np.array([[100.0], [0.4]])
    targets = np.array([100.0, 0.1])
    bounds = np.array([np.inf])
    symmetric, _ = goal.solve_goal_weights(matrix, targets, bounds, np.ones(2), "symmetric")
    under_x4, _ = goal.solve_goal_weights(
        matrix,
        targets,
        bounds,
        np.ones(2),
        "symmetric",
        underfill_factor=4.0,
    )

    symmetric_n_underfill = max(0.0, float(targets[0] - matrix[0] @ symmetric))
    weighted_n_underfill = max(0.0, float(targets[0] - matrix[0] @ under_x4))
    assert weighted_n_underfill < symmetric_n_underfill


def test_goal_solver_uses_corrected_golden_s_target_without_dominance() -> None:
    root = Path(__file__).resolve().parents[1]
    recipe = yaml.safe_load((root / "recipes" / "solve_golden.yml").read_text(encoding="utf-8"))
    recipe["solver_config"] = {
        "nitrogen_objective_mode": "n_total_only",
        "s_objective_enabled": True,
    }
    water = load_water_profile_data(root / "data" / "water_profiles" / "65936.yml")

    solved = goal.solve_goal_recipe_data(
        recipe,
        goal.GoalPolicy("test", "mmol", "symmetric"),
        ferts=load_fertilizers(),
        mm=load_molar_masses(),
        water_profile_data=water,
    )

    assert "S" in solved.result.objective_elements
    assert solved.result.targets_mg_l["S"] == pytest.approx(85.79586471044226)
    assert solved.pareto_dominated is False
    assert all(float(item["grams"]) >= 0.0 for item in solved.result.fertilizers)


def test_model_matrix_keeps_historical_34191_on_legacy_runtime() -> None:
    root = Path(__file__).resolve().parents[1]
    cases = yaml.safe_load((root / "scripts" / "solver_matrix_cases.yml").read_text(encoding="utf-8"))
    policy = next(item for item in model_matrix.model_policies(cases) if item.policy_id == "legacy_34191")

    assert policy.solver_config is not None
    assert policy.solver_config["solver_model"] == "nnls_tuning"


def test_goal_model_matrix_smoke_passes_quality_gate(tmp_path: Path) -> None:
    exit_code = model_matrix.main(
        [
            "--profiles",
            "solve_golden",
            "--portfolio-ids",
            "solve_golden",
            "--out-dir",
            str(tmp_path),
        ]
    )

    summary = json.loads((tmp_path / "model_matrix_summary.json").read_text(encoding="utf-8"))
    assert exit_code == 0
    assert summary["completed_rows"] == 64
    assert summary["failed_rows"] == 0
    assert summary["quality_gate"]["passed"] is True
    assert summary["quality_gate"]["production_policy"] == "mass_nnls"
    assert (tmp_path / "model_matrix_rows.jsonl.gz").exists()
