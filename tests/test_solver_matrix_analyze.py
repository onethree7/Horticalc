from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "solver_matrix_analyze",
    ROOT / "scripts" / "solver_matrix_analyze.py",
)
solver_matrix_analyze = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules["solver_matrix_analyze"] = solver_matrix_analyze
SPEC.loader.exec_module(solver_matrix_analyze)


FIELDS = [
    "profile_id",
    "profile_name",
    "phase",
    "nitrogen_objective_mode",
    "subset_size",
    "fertilizers_allowed",
    "config_name",
    "solver_config",
    "status",
    "composite_score",
    "macro_score",
    "n_form_score",
    "micro_score",
    "other_score",
    "ignored_score",
    "max_error_key",
    "max_error_score",
    "total_grams",
    "used_fertilizer_count",
    "used_fertilizers",
    "ignored_targets",
]


def _write_run(run_dir: Path, rows: list[dict[str, object]]) -> None:
    run_dir.mkdir()
    summary = {
        "total_runs": len(rows),
        "failed_runs": 0,
        "profiles": ["profile_a"],
        "allowed_fertilizers": ["Fert A", "Fert B"],
        "nitrogen_objective_modes": ["n_total_only", "n_forms_only"],
        "best_by_profile": {"profile_a": {"composite_score": 20.0}},
    }
    (run_dir / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    with (run_dir / "results.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        for row in rows:
            normalized = {
                field: row.get(field, "")
                for field in FIELDS
            }
            for field in ["fertilizers_allowed", "solver_config", "used_fertilizers", "ignored_targets"]:
                if not isinstance(normalized[field], str):
                    normalized[field] = json.dumps(normalized[field])
            writer.writerow(normalized)


def test_analyze_run_extracts_feature_and_fertilizer_effects(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    _write_run(
        run_dir,
        [
            {
                "profile_id": "profile_a",
                "profile_name": "Profile A",
                "phase": "base",
                "nitrogen_objective_mode": "n_total_only",
                "subset_size": 1,
                "fertilizers_allowed": ["Fert A"],
                "config_name": "n_mode=n_total_only",
                "solver_config": {
                    "relative_weighting": True,
                    "singleton_supplier_enabled": True,
                    "singleton_underfill_enabled": True,
                    "n_total_governor_enabled": False,
                },
                "status": "ok",
                "composite_score": 10.0,
                "macro_score": 2.0,
                "micro_score": 1.0,
                "max_error_key": "Cu",
                "max_error_score": 5.0,
                "fertilizers_allowed": ["Fert A"],
                "used_fertilizers": [],
                "ignored_targets": {"HCO3": {}},
            },
            {
                "profile_id": "profile_a",
                "profile_name": "Profile A",
                "phase": "base",
                "nitrogen_objective_mode": "n_total_only",
                "subset_size": 1,
                "fertilizers_allowed": ["Fert B"],
                "config_name": "n_mode=n_total_only,singleton_supplier_enabled=false",
                "solver_config": {
                    "relative_weighting": True,
                    "singleton_supplier_enabled": False,
                    "singleton_underfill_enabled": True,
                    "n_total_governor_enabled": False,
                },
                "status": "ok",
                "composite_score": 30.0,
                "macro_score": 4.0,
                "micro_score": 3.0,
                "max_error_key": "B",
                "max_error_score": 8.0,
                "used_fertilizers": [],
                "ignored_targets": {},
            },
        ],
    )

    analysis = solver_matrix_analyze.analyze_run(run_dir, top_limit=5)

    assert analysis["counts"]["status"] == {"ok": 2}
    assert analysis["best_final_by_profile"]["profile_a"]["score"] == 10.0
    supplier_stats = analysis["base_flag_effects_by_mode"]["n_total_only"]["singleton_supplier_enabled"]
    assert supplier_stats["true"]["avg"] == 10.0
    assert supplier_stats["false"]["avg"] == 30.0
    fert_effect = analysis["fertilizer_effect_base_by_mode"]["n_total_only"]
    fert_a = next(row for row in fert_effect if row["fertilizer"] == "Fert A")
    assert fert_a["omission_delta"] == 20.0


def test_write_markdown_report(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    _write_run(
        run_dir,
        [
            {
                "profile_id": "profile_a",
                "phase": "base",
                "nitrogen_objective_mode": "n_total_only",
                "subset_size": 1,
                "fertilizers_allowed": ["Fert A"],
                "config_name": "n_mode=n_total_only",
                "solver_config": {},
                "status": "ok",
                "composite_score": 10.0,
                "macro_score": 2.0,
                "micro_score": 1.0,
                "max_error_key": "Cu",
                "max_error_score": 5.0,
                "used_fertilizers": [],
                "ignored_targets": {},
            }
        ],
    )
    analysis = solver_matrix_analyze.analyze_run(run_dir, top_limit=5)
    out_md = tmp_path / "report.md"

    solver_matrix_analyze.write_markdown_report(analysis, out_md)

    text = out_md.read_text(encoding="utf-8")
    assert "# Solver Matrix Analysis" in text
    assert "`n_total_only`" in text
