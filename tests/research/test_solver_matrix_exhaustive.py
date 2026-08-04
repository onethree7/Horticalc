from __future__ import annotations

import itertools
import json
import sqlite3
import zlib
from pathlib import Path

import numpy as np
import pytest

import scripts.solver_matrix as solver_matrix
import scripts.solver_matrix_exhaustive as exhaustive

pytestmark = pytest.mark.research


def _cases() -> dict:
    return solver_matrix._read_yaml(solver_matrix.DEFAULT_CASES_PATH)


def test_exhaustive_catalog_is_conditionally_reduced_and_covers_requested_interaction() -> None:
    cases = _cases()

    assert solver_matrix.exhaustive_solver_config_count(cases) == 354_523
    configs = list(itertools.islice(solver_matrix.iter_exhaustive_solver_configs(cases), 1_000))
    assert len({config.config_id for config in configs}) == len(configs)
    assert any(
        config.values["relative_weighting"] is False
        and config.values["singleton_supplier_enabled"] is True
        and config.values["singleton_underfill_enabled"] is True
        and config.values["singleton_share_threshold"] == 0.85
        and config.values["singleton_underfill_share_threshold"] == 0.0
        and config.values["singleton_underfill_max_iter"] == 2
        and config.values["singleton_max_regress_pp"] == 10.0
        and config.values["s_objective_enabled"] is True
        and config.values["nitrogen_objective_mode"] == "n_total_only"
        for config in configs
    )


def test_pareto_mask_is_exact_and_keeps_equal_nondominated_points() -> None:
    costs = np.array(
        [
            [1.0, 1.0],
            [2.0, 2.0],
            [0.5, 3.0],
            [3.0, 0.5],
            [1.0, 1.0],
        ]
    )

    assert exhaustive.pareto_efficient_mask(costs).tolist() == [True, False, True, True, True]


def test_exhaustive_smoke_is_compact_deterministic_and_resumable(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    arguments = [
        "--max-configs",
        "4",
        "--profiles",
        "Hoagland_Arnon_1950_Solution1_Nitrate",
        "--workers",
        "1",
        "--queue-depth",
        "2",
        "--commit-every",
        "2",
        "--finalists-per-profile",
        "2",
        "--out-dir",
        str(tmp_path),
    ]

    assert exhaustive.main(arguments) == 0
    assert "Pareto analysis complete: 1 profiles" in capsys.readouterr().out
    database = tmp_path / "exhaustive.sqlite3"
    assert database.exists()
    assert (tmp_path / "pareto_analysis.json").exists()

    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT COUNT(*) FROM configs").fetchone()[0] == 4
        assert connection.execute("SELECT COUNT(*) FROM runs").fetchone()[0] == 4
        assert connection.execute("SELECT COUNT(*) FROM solutions").fetchone()[0] <= 4
        representative_id, representative_hash = connection.execute(
            """
            SELECT p.representative_config_id, c.config_hash
            FROM pareto AS p
            JOIN configs AS c ON c.config_id = p.representative_config_id
            WHERE p.is_knee = 1
            """
        ).fetchone()
        expected_id = connection.execute(
            "SELECT MIN(config_id) FROM runs WHERE solution_id = (SELECT solution_id FROM pareto WHERE is_knee = 1)"
        ).fetchone()[0]
        expected_hash = connection.execute(
            "SELECT config_hash FROM configs WHERE config_id = ?", (expected_id,)
        ).fetchone()[0]
        assert (representative_id, representative_hash) == (expected_id, expected_hash)
        finalist_payload = connection.execute(
            "SELECT full_result_zlib FROM finalists WHERE selection = 'pareto_utopia' AND rank = 1"
        ).fetchone()[0]
        finalist = json.loads(zlib.decompress(finalist_payload))
        assert finalist["status"] == "ok"
        assert json.loads(finalist["solver_config"])["s_objective_enabled"] is True

    first_summary = json.loads((tmp_path / "exhaustive_summary.json").read_text(encoding="utf-8"))
    analysis = json.loads((tmp_path / "pareto_analysis.json").read_text(encoding="utf-8"))
    assert first_summary["executed_configs_this_invocation"] == 4
    assert first_summary["status"] == "complete"
    assert analysis["global_selection"]["complete_config_count"] == 4
    assert analysis["global_selection"]["objective_coordinate_count"] > 0
    assert analysis["global_selection"]["utopia"]["solver_config"]["s_objective_enabled"] is True

    assert exhaustive.main(arguments) == 0
    capsys.readouterr()
    resumed = json.loads((tmp_path / "exhaustive_summary.json").read_text(encoding="utf-8"))
    assert resumed["resumed"] is True
    assert resumed["executed_configs_this_invocation"] == 0
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT COUNT(*) FROM runs").fetchone()[0] == 4
