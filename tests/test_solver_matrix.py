from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "src"))

SPEC = importlib.util.spec_from_file_location("solver_matrix", ROOT / "scripts" / "solver_matrix.py")
solver_matrix = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules["solver_matrix"] = solver_matrix
SPEC.loader.exec_module(solver_matrix)


def test_resolve_allowed_fertilizers_rejects_whitespace_with_hint() -> None:
    fertilizers = {
        "Compo Fetrilon Combi 1": object(),
        "Yara Tera CALCINIT": object(),
    }

    with pytest.raises(ValueError) as exc_info:
        solver_matrix.resolve_allowed_fertilizers(
            ["Compo Fetrilon Combi 1 ", "Yara Tera CALCINIT"],
            fertilizers,
        )

    message = str(exc_info.value)
    assert "without surrounding whitespace" in message
    assert "'Compo Fetrilon Combi 1'" in message


def test_score_solution_follows_solver_objective_elements() -> None:
    targets = {
        "K": 0.0,
        "Fe": 1.0,
        "S": 100.0,
        "HCO3": 0.0,
    }
    achieved = {
        "K": 2.0,
        "Fe": 1.1,
        "S": 1000.0,
        "HCO3": 100.0,
    }

    score = solver_matrix.score_solution(targets, achieved, objective_elements=["Fe"])
    same_without_ignored_overshoot = solver_matrix.score_solution(
        targets,
        {**achieved, "K": 0.0, "S": 100.0, "HCO3": 0.0},
        objective_elements=["Fe"],
    )

    assert score["elements"]["K"]["category"] == "ignored"
    assert score["elements"]["S"]["category"] == "ignored"
    assert score["elements"]["HCO3"]["category"] == "ignored"
    assert score["ignored_score"] > same_without_ignored_overshoot["ignored_score"]
    assert score["composite_score"] == same_without_ignored_overshoot["composite_score"]


def test_score_solution_scores_zero_target_when_solver_objective_includes_it() -> None:
    score = solver_matrix.score_solution(
        {"K": 0.0},
        {"K": 2.0},
        objective_elements=["K"],
    )

    assert score["elements"]["K"]["category"] == "macro"
    assert score["elements"]["K"]["error_percent"] is None
    assert score["elements"]["K"]["score"] == 100.0
    assert score["composite_score"] == 300.0


def test_score_solution_scores_hco3_when_solver_objective_includes_it() -> None:
    score = solver_matrix.score_solution(
        {"HCO3": 10.0},
        {"HCO3": 15.0},
        objective_elements=["HCO3"],
    )

    assert score["elements"]["HCO3"]["category"] == "other"
    assert score["elements"]["HCO3"]["score"] == 50.0
    assert score["composite_score"] == 25.0


def test_boolean_solver_configs_include_requested_nitrogen_modes() -> None:
    configs = solver_matrix.boolean_solver_configs(["n_total_only", "n_forms_only"])

    assert len(configs) == 128
    assert {config.values["nitrogen_objective_mode"] for config in configs} == {
        "n_total_only",
        "n_forms_only",
    }
    assert all(config.name.startswith("n_mode=") for config in configs)


def test_boolean_solver_configs_start_with_current_simple_default() -> None:
    first = solver_matrix.boolean_solver_configs(["n_total_only"])[0]

    assert first.values == {
        "relative_weighting": True,
        "macro_priority_enabled": False,
        "stage_optimization_enabled": False,
        "singleton_supplier_enabled": True,
        "singleton_underfill_enabled": True,
        "n_total_governor_enabled": False,
        "nitrogen_objective_mode": "n_total_only",
    }
    assert first.name == "n_mode=n_total_only"


def test_solver_matrix_quick_smoke(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = solver_matrix.main(
        [
            "--preset",
            "quick",
            "--profiles",
            "Hoagland_Arnon_1950_Solution1_Nitrate",
            "--max-configs",
            "2",
            "--out-dir",
            str(tmp_path),
        ]
    )

    assert exit_code == 0
    assert "Solver matrix complete" in capsys.readouterr().out

    results_csv = tmp_path / "results.csv"
    results_jsonl = tmp_path / "results.jsonl"
    summary_json = tmp_path / "summary.json"
    assert results_csv.exists()
    assert results_jsonl.exists()
    assert summary_json.exists()

    summary = json.loads(summary_json.read_text(encoding="utf-8"))
    assert summary["total_runs"] == 2
    assert summary["failed_runs"] == 0
    assert "Hoagland_Arnon_1950_Solution1_Nitrate" in summary["best_by_profile"]


def test_solver_matrix_max_runs_stops_early(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = solver_matrix.main(
        [
            "--preset",
            "quick",
            "--profiles",
            "Hoagland_Arnon_1950_Solution1_Nitrate",
            "--max-runs",
            "1",
            "--out-dir",
            str(tmp_path),
        ]
    )

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "Stopped early at --max-runs 1" in output

    summary = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert summary["total_runs"] == 1
    assert summary["stopped_early"] is True
