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


def test_score_solution_handles_zero_targets_and_ignored_targets() -> None:
    targets = {
        "K": 0.0,
        "Fe": 1.0,
        "S": 100.0,
    }
    achieved = {
        "K": 2.0,
        "Fe": 1.1,
        "S": 1000.0,
    }

    score = solver_matrix.score_solution(targets, achieved, objective_elements=["K", "Fe"])
    same_without_ignored_overshoot = solver_matrix.score_solution(
        targets,
        {**achieved, "S": 100.0},
        objective_elements=["K", "Fe"],
    )

    assert score["elements"]["K"]["error_percent"] is None
    assert score["elements"]["K"]["score"] == 100.0
    assert score["elements"]["S"]["category"] == "ignored"
    assert score["ignored_score"] > same_without_ignored_overshoot["ignored_score"]
    assert score["composite_score"] == same_without_ignored_overshoot["composite_score"]


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
