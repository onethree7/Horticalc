from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from types import SimpleNamespace

import numpy as np

import scripts.solver_matrix as solver_matrix
import scripts.solver_matrix_exhaustive as exhaustive
import scripts.solver_preference as preference
import scripts.solver_preference_barrage as barrage
import scripts.solver_preference_screen as screen


def _solution(
    *,
    n_error: float,
    cu_error: float,
    solution_hash: str = "solution",
) -> dict:
    return {
        "solution_id": 1,
        "solution_hash": solution_hash,
        "config_id": 1,
        "config_hash": "config",
        "solver_config": {},
        "targets_mg_per_l": {"N_total": 100.0, "Cu": 0.05},
        "achieved_mg_per_l": {"N_total": 100.0 + n_error, "Cu": 0.05 + cu_error},
        "signed_errors_mg_per_l": {"N_total": n_error, "Cu": cu_error},
        "reachable_error_span_mg_per_l": {"N_total": 50.0, "Cu": 0.5},
    }


def test_raw_features_preserve_units_direction_and_reachability() -> None:
    features = preference.raw_features(
        _solution(n_error=-30.0, cu_error=0.15),
        ("N_total", "Cu"),
    )

    assert features["N_total:under_mg"] == 30.0
    assert features["N_total:under_relative"] == 0.3
    assert features["N_total:under_reachable"] == 0.6
    assert features["N_total:over_mg"] == 0.0
    assert features["Cu:over_mg"] == 0.15
    assert np.isclose(features["Cu:over_relative"], 3.0)
    assert np.isclose(features["Cu:over_reachable"], 0.3)


def test_pair_orientation_is_canonical() -> None:
    database = SimpleNamespace(signature="matrix")
    high = _solution(n_error=-1.0, cu_error=0.0, solution_hash="z")
    low = _solution(n_error=-2.0, cu_error=0.0, solution_hash="a")

    forward = preference._pair_record(database, "profile", high, low, 1.0)
    reverse = preference._pair_record(database, "profile", low, high, 1.0)

    assert forward["pair_id"] == reverse["pair_id"]
    assert forward["a"]["solution_hash"] == "a"
    assert forward["b"]["solution_hash"] == "z"

    predicted = preference._pair_record(
        database,
        "profile",
        high,
        low,
        1.0,
        selection="model_uncertainty",
        predicted_probability_a=0.8,
    )
    assert np.isclose(predicted["predicted_preference_probability_a"], 0.2)


def test_pair_table_uses_nutrient_order_mg_per_l_and_plain_decimals() -> None:
    solution_a = _solution(n_error=-2.2, cu_error=0.09068, solution_hash="a")
    solution_b = _solution(n_error=-0.2702, cu_error=0.2342, solution_hash="b")
    for solution, bor_error in ((solution_a, -0.09267), (solution_b, 0.4241)):
        solution["targets_mg_per_l"]["B"] = 0.44
        solution["achieved_mg_per_l"]["B"] = 0.44 + bor_error
        solution["signed_errors_mg_per_l"]["B"] = bor_error
    pair = {"pair_id": "pair", "a": solution_a, "b": solution_b}

    table = preference._format_pair_table(pair)

    assert "Alle Konzentrationen und Differenzen sind in mg/L." in table
    assert table.index("N gesamt") < table.index("Cu") < table.index("Bor")
    assert "A erreicht" in table
    assert "A Differenz" in table
    assert "-2.200" in table
    assert "+0.09068" in table
    assert "-2.20 %" in table
    assert "e-" not in table.lower()


def test_monotone_model_learns_preference_without_negative_penalties() -> None:
    pairs = []
    labels = {}
    for index in range(20):
        preferred = _solution(
            n_error=-1.0 - index / 20,
            cu_error=0.2 + index / 100,
            solution_hash=f"a-{index}",
        )
        rejected = _solution(
            n_error=-20.0 - index,
            cu_error=0.0,
            solution_hash=f"b-{index}",
        )
        pair = {
            "pair_id": f"pair-{index}",
            "matrix_signature": "matrix",
            "profile_id": "profile",
            "a": preferred,
            "b": rejected,
        }
        pairs.append(pair)
        labels[pair["pair_id"]] = {
            "pair_id": pair["pair_id"],
            "matrix_signature": "matrix",
            "choice": "A",
        }

    model = preference.train_model(
        pairs,
        labels,
        ("N_total", "Cu"),
        l1=0.001,
        l2=0.01,
        iterations=2_000,
        learning_rate=0.15,
    )

    assert model["training"]["accuracy"] == 1.0
    assert all(weight >= 0.0 for weight in model["weights"])
    assert preference.solution_cost(pairs[0]["a"], model) < preference.solution_cost(pairs[0]["b"], model)


def test_grouped_model_shares_one_severity_across_physical_views() -> None:
    pairs = []
    labels = {}
    for index in range(8):
        preferred = _solution(n_error=-1.0, cu_error=0.2, solution_hash=f"ga-{index}")
        rejected = _solution(n_error=-20.0 - index, cu_error=0.0, solution_hash=f"gb-{index}")
        pair = {
            "pair_id": f"group-{index}",
            "matrix_signature": "matrix",
            "profile_id": "profile",
            "a": preferred,
            "b": rejected,
        }
        pairs.append(pair)
        labels[pair["pair_id"]] = {
            "pair_id": pair["pair_id"],
            "matrix_signature": "matrix",
            "choice": "A",
        }

    model = preference.train_model(
        pairs,
        labels,
        ("N_total", "Cu"),
        l1=0.0,
        l2=0.02,
        iterations=2_000,
        learning_rate=0.15,
        feature_structure="grouped",
    )

    assert model["feature_structure"] == "grouped"
    assert model["design_diagnostics"]["columns"] < len(model["features"])
    assert model["design_diagnostics"]["rank"] <= model["design_diagnostics"]["columns"]
    severity = next(row for row in model["learned_severities"] if row["element_direction"] == "N_total:under")
    indices = [
        model["features"].index(f"N_total:{suffix}") for suffix in ("under_mg", "under_relative", "under_reachable")
    ]
    assert all(np.isclose(model["weights"][index], severity["weight"] / 3.0) for index in indices)
    assert preference.solution_cost(pairs[0]["a"], model) < preference.solution_cost(pairs[0]["b"], model)


def _preference_database(path: Path) -> None:
    element_order = ("N_total", "Cu")
    profiles = [
        {
            "profile_id": profile_id,
            "targets_mg_per_l": {"N_total": 100.0, "Cu": 0.05},
        }
        for profile_id in ("p1", "p2")
    ]
    manifest = {
        "signature": "matrix",
        "element_order": list(element_order),
        "profiles": profiles,
        "portfolio": {"portfolio_id": "primary"},
    }
    with sqlite3.connect(path) as connection:
        connection.executescript(
            """
            CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE profiles(profile_id TEXT PRIMARY KEY, objective_elements_json TEXT);
            CREATE TABLE configs(config_id INTEGER PRIMARY KEY, config_hash TEXT, values_json TEXT);
            CREATE TABLE solutions(solution_id INTEGER PRIMARY KEY, solution_hash TEXT, achieved_vector BLOB);
            CREATE TABLE runs(
                config_id INTEGER, profile_id TEXT, portfolio_id TEXT,
                solution_id INTEGER, status TEXT
            );
            CREATE TABLE pareto(
                profile_id TEXT, portfolio_id TEXT, solution_id INTEGER,
                representative_config_id INTEGER, is_knee INTEGER, utopia_distance REAL
            );
            """
        )
        connection.execute("INSERT INTO meta VALUES ('manifest', ?)", (json.dumps(manifest),))
        connection.executemany(
            "INSERT INTO profiles VALUES (?, ?)",
            [(profile["profile_id"], json.dumps(element_order)) for profile in profiles],
        )
        connection.executemany(
            "INSERT INTO configs VALUES (?, ?, ?)",
            [(1, "good", "{}"), (2, "bad", "{}")],
        )
        solutions = [
            (1, "good", np.array([98.0, 0.35], dtype="<f8").tobytes()),
            (2, "bad", np.array([75.0, 0.05], dtype="<f8").tobytes()),
        ]
        connection.executemany("INSERT INTO solutions VALUES (?, ?, ?)", solutions)
        for profile_id in ("p1", "p2"):
            connection.executemany(
                "INSERT INTO runs VALUES (?, ?, 'primary', ?, 'ok')",
                [(1, profile_id, 1), (2, profile_id, 2)],
            )
            connection.executemany(
                "INSERT INTO pareto VALUES (?, 'primary', ?, ?, 0, 1.0)",
                [(profile_id, 1, 1), (profile_id, 2, 2)],
            )


def test_rank_is_noncompensatory_and_scores_unique_solutions(tmp_path: Path) -> None:
    database_path = tmp_path / "matrix.sqlite3"
    _preference_database(database_path)
    names = preference.feature_names(("N_total", "Cu"))
    weights = [0.0] * len(names)
    weights[names.index("N_total:under_mg")] = 1.0
    weights[names.index("Cu:over_mg")] = 0.01
    model = {
        "matrix_signature": "matrix",
        "features": list(names),
        "scales": [1.0] * len(names),
        "weights": weights,
    }

    database = preference.MatrixDatabase(database_path)
    try:
        ranking = preference.rank_configurations(database, model, top=2)
    finally:
        database.close()

    assert [row["config_id"] for row in ranking["ranking"]] == [1, 2]
    assert ranking["ranking"][0]["worst_element"]["element"] == "N_total"
    assert ranking["selection"].startswith("lexicographic worst learned element penalty")


def test_portfolio_barrage_is_compact_resumable_and_reports_holdouts(
    tmp_path: Path,
) -> None:
    cases = solver_matrix._read_yaml(solver_matrix.DEFAULT_CASES_PATH)
    profile_id = "Hoagland_Arnon_1950_Solution1_Nitrate"
    config = solver_matrix.resolve_solver_config(cases["solver_baseline"])
    ranking_path = tmp_path / "ranking.json"
    model_path = tmp_path / "model.json"
    ranking_path.write_text(
        json.dumps(
            {
                "matrix_signature": "synthetic-matrix",
                "ranking": [
                    {
                        "config_id": 1,
                        "config_hash": "baseline",
                        "solver_config": config,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    names = preference.feature_names(("N_total",))
    model_path.write_text(
        json.dumps(
            {
                "matrix_signature": "synthetic-matrix",
                "features": list(names),
                "scales": [1.0] * len(names),
                "weights": [1.0 if name == "N_total:under_mg" else 0.0 for name in names],
                "profile_contexts": {profile_id: {"reachable_error_span_mg_per_l": {"N_total": 100.0}}},
            }
        ),
        encoding="utf-8",
    )
    out_dir = tmp_path / "barrage"
    arguments = [
        "--ranking",
        str(ranking_path),
        "--model",
        str(model_path),
        "--out-dir",
        str(out_dir),
        "--top",
        "1",
        "--profiles",
        profile_id,
        "--workers",
        "1",
        "--queue-depth",
        "2",
        "--bootstrap-samples",
        "5",
    ]

    assert barrage.main(arguments) == 0
    summary = json.loads((out_dir / "barrage_summary.json").read_text(encoding="utf-8"))
    analysis = json.loads((out_dir / "barrage_ranking.json").read_text(encoding="utf-8"))
    assert summary["planned_solves"] == 35
    assert summary["total_runs"] == 35
    assert summary["status"] == "complete"
    assert analysis["case_count"] == 33
    assert analysis["total_case_count"] == 35
    assert analysis["diagnostic_case_count"] == 2
    assert analysis["ranking"][0]["diagnostic"]["case_count"] == 2
    assert len(analysis["ranking"][0]["leave_one_portfolio_out_ranks"]) == 33
    with sqlite3.connect(out_dir / "preference_barrage.sqlite3") as connection:
        assert connection.execute("SELECT COUNT(*) FROM runs").fetchone()[0] == 35
        assert connection.execute("SELECT COUNT(*) FROM solutions").fetchone()[0] <= 35

    assert barrage.main(arguments) == 0
    resumed = json.loads((out_dir / "barrage_summary.json").read_text(encoding="utf-8"))
    assert resumed["resumed"] is True
    assert resumed["executed_tasks_this_invocation"] == 0


def test_barrage_competition_ranks_do_not_split_exact_ties() -> None:
    config_ids = np.array([3, 1, 2])
    element_costs = np.array([[1.0, 2.0], [1.0, 2.0], [1.0, 3.0]])
    total_costs = np.array([[2.0, 3.0], [2.0, 3.0], [2.0, 4.0]])
    mask = np.array([True, True])

    order, metrics = barrage._rank_metrics(config_ids, element_costs, total_costs, mask)
    ranks = barrage._competition_ranks(order, metrics)

    assert order.tolist() == [1, 0, 2]
    assert ranks.tolist() == [1, 1, 3]


def test_barrage_collapsed_ranks_count_behaviors_not_duplicate_configs() -> None:
    config_ids = np.array([10, 11, 20])
    element_costs = np.array([[1.0], [1.0], [2.0]])
    total_costs = np.array([[1.0], [1.0], [2.0]])
    representatives = np.array([0, 2])
    behavior_index = np.array([0, 0, 1])

    ranks, _ = barrage._collapsed_ranks(
        config_ids,
        element_costs,
        total_costs,
        np.array([True]),
        representatives,
        behavior_index,
    )

    assert ranks.tolist() == [1, 1, 2]


def test_barrage_diagnostic_portfolio_cannot_change_selection_rank() -> None:
    portfolios = (
        solver_matrix.FertilizerPortfolio("real", "", ("A",), evaluation_role="selection"),
        solver_matrix.FertilizerPortfolio("humin", "", ("H",), evaluation_role="diagnostic"),
    )
    selection_mask, diagnostic_mask = barrage._case_role_masks([("profile", "real"), ("profile", "humin")], portfolios)
    element_costs = np.array([[1.0, 100.0], [2.0, 0.0]])
    total_costs = element_costs.copy()

    selection_order, _ = barrage._rank_metrics(np.array([1, 2]), element_costs, total_costs, selection_mask)
    contaminated_order, _ = barrage._rank_metrics(
        np.array([1, 2]), element_costs, total_costs, selection_mask | diagnostic_mask
    )

    assert selection_order.tolist() == [0, 1]
    assert contaminated_order.tolist() == [1, 0]


def test_analysis_compatibility_ignores_model_and_source_hashes(tmp_path: Path) -> None:
    connection = sqlite3.connect(tmp_path / "analysis.sqlite3")
    stored = {
        "schema_version": 1,
        "source_matrix_signature": "matrix",
        "shortlist_config_count": 1,
        "shortlist_sha256": "shortlist",
        "profiles": [{"profile_id": "p"}],
        "portfolios": [{"portfolio_id": "f"}],
        "fertilizers": {},
        "molar_masses": {},
        "water_profile_name": "water",
        "water_profile_data": {},
        "osmosis_percent": 100.0,
        "liters": 10.0,
        "element_order": ["N_total"],
        "planned_solves": 1,
        "preference_model_sha256": "old-model",
        "source_sha256": "old-source",
    }
    connection.execute("CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    connection.execute("INSERT INTO meta VALUES ('manifest', ?)", (json.dumps(stored),))
    changed = {**stored, "preference_model_sha256": "new-model", "source_sha256": "new-source"}
    context = barrage.BarrageContext(
        profiles=(),
        portfolios=(),
        configs=(),
        fertilizers={},
        molar_masses={},
        water_profile_name="water",
        water_profile_data={},
        osmosis_percent=100.0,
        liters=10.0,
        element_order=("N_total",),
        signature="new-signature",
        manifest=changed,
    )

    assert barrage._stored_analysis_inputs_match(connection, context)
    context.manifest["liters"] = 20.0
    assert not barrage._stored_analysis_inputs_match(connection, context)
    connection.close()


def test_all_config_screen_is_compact_resumable_and_selects_union(
    tmp_path: Path,
) -> None:
    profile_id = "Hoagland_Arnon_1950_Solution1_Nitrate"
    source_dir = tmp_path / "source"
    assert (
        exhaustive.main(
            [
                "--max-configs",
                "4",
                "--profiles",
                profile_id,
                "--workers",
                "1",
                "--skip-analysis",
                "--out-dir",
                str(source_dir),
            ]
        )
        == 0
    )
    source_database = source_dir / "exhaustive.sqlite3"
    with sqlite3.connect(source_database) as connection:
        signature = connection.execute("SELECT value FROM meta WHERE key = 'signature'").fetchone()[0]
    names = preference.feature_names(("N_total",))
    model_path = tmp_path / "model.json"
    model_path.write_text(
        json.dumps(
            {
                "matrix_signature": signature,
                "features": list(names),
                "scales": [1.0] * len(names),
                "weights": [1.0 if name == "N_total:under_mg" else 0.0 for name in names],
                "profile_contexts": {profile_id: {"reachable_error_span_mg_per_l": {"N_total": 100.0}}},
            }
        ),
        encoding="utf-8",
    )
    out_dir = tmp_path / "screen"
    arguments = [
        "--source-database",
        str(source_database),
        "--model",
        str(model_path),
        "--profiles",
        profile_id,
        "--portfolio-ids",
        "solve_golden,restricted_313_bittersalz_mkp",
        "--workers",
        "1",
        "--queue-depth",
        "2",
        "--lex-top",
        "2",
        "--worst-case-top",
        "2",
        "--mean-top",
        "2",
        "--per-portfolio-top",
        "1",
        "--per-profile-top",
        "1",
        "--per-portfolio-holdout-top",
        "1",
        "--per-profile-holdout-top",
        "1",
        "--out-dir",
        str(out_dir),
    ]

    assert screen.main(arguments) == 0
    summary = json.loads((out_dir / "screening_summary.json").read_text(encoding="utf-8"))
    ranking = json.loads((out_dir / "screening_ranking.json").read_text(encoding="utf-8"))
    assert summary["planned_solves"] == 8
    assert summary["status"] == "complete"
    assert 1 <= ranking["selected_configurations"] <= 4
    assert all(row["selection_reasons"] for row in ranking["ranking"])

    assert screen.main(arguments) == 0
    resumed = json.loads((out_dir / "screening_summary.json").read_text(encoding="utf-8"))
    assert resumed["resumed"] is True
    assert resumed["executed_tasks_this_invocation"] == 0
