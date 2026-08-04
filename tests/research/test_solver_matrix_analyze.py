from __future__ import annotations

from pathlib import Path

import pytest

import scripts.solver_matrix as solver_matrix
import scripts.solver_matrix_analyze as solver_matrix_analyze

pytestmark = pytest.mark.research


def _write_deep_fixture(run_dir: Path) -> None:
    exit_code = solver_matrix.main(
        [
            "--preset",
            "deep",
            "--profiles",
            "Hoagland_Arnon_1950_Solution1_Nitrate",
            "--max-configs",
            "3",
            "--out-dir",
            str(run_dir),
        ]
    )
    assert exit_code == 0


def test_analyze_run_extracts_paired_setting_and_omission_effects(tmp_path: Path) -> None:
    _write_deep_fixture(tmp_path)

    analysis = solver_matrix_analyze.analyze_run(tmp_path, top_limit=5)

    assert analysis["schema_version"] == 2
    assert analysis["counts"]["status"] == {"ok": 38}
    assert analysis["baseline_by_profile"]["Hoagland_Arnon_1950_Solution1_Nitrate"]["score"] > 0
    assert "boolean_factorial" in analysis["setting_effects"]
    assert "relative_weighting" in analysis["setting_effects"]["boolean_factorial"]
    assert len(analysis["mass_barrage_portfolios"]) == 33
    assert len(analysis["diagnostic_portfolios"]) == 2
    assert len(analysis["fertilizer_omission_impact"]) == 22
    omitted = {row["fertilizer"] for row in analysis["fertilizer_omission_impact"]}
    assert "HuminTech AMINO POWER Plus Liquid" not in omitted
    assert "HuminTech Fulvital Plus Liquid" not in omitted


def test_write_markdown_report_is_self_explanatory(tmp_path: Path) -> None:
    _write_deep_fixture(tmp_path)
    analysis = solver_matrix_analyze.analyze_run(tmp_path, top_limit=5)
    out_md = tmp_path / "report.md"

    solver_matrix_analyze.write_markdown_report(analysis, out_md)

    text = out_md.read_text(encoding="utf-8")
    assert "# Solver Matrix Analysis" in text
    assert "Nitrogen objective | `n_total_only`" in text
    assert "Elemental S objective | `true`" in text
    assert "Controlled Setting Effects" in text
    assert "Nutrient-Portfolio Mass Barrage" in text
    assert "Leave-One-Out Fertilizer Impact" in text
    assert "Diagnostic Honeypot Portfolios" in text
    assert "Unresolved requested profiles" not in text
