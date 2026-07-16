from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import sys
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterator

for _thread_variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_thread_variable, "1")

import numpy as np  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.solver_matrix as matrix  # noqa: E402
import scripts.solver_matrix_exhaustive as exhaustive  # noqa: E402
import scripts.solver_preference as preference  # noqa: E402
import scripts.solver_preference_barrage as barrage  # noqa: E402
from horticalc.data_io import (  # noqa: E402
    load_fertilizers,
    load_molar_masses,
    load_water_profile_data,
)
from horticalc.paths import logs_dir, resolve_water_profile_path  # noqa: E402

SCHEMA_VERSION = 1
DEFAULT_OUT_DIR = logs_dir(ROOT) / "solver_matrix" / "preference_screen"
DEFAULT_PORTFOLIO_IDS = (
    "solve_golden",
    "restricted_blossom_fetrilon_pekacid_spezial",
    "restricted_313_bittersalz_mkp",
)


def _source_contract(
    args: argparse.Namespace,
    model: dict[str, Any],
) -> tuple[str, int]:
    database = preference.MatrixDatabase(args.source_database)
    try:
        if str(model["matrix_signature"]) != database.signature:
            raise ValueError("Preference model and exhaustive source signatures differ")
        count = int(database.connection.execute("SELECT COUNT(*) FROM configs").fetchone()[0])
        if args.max_configs is not None:
            count = min(count, args.max_configs)
        return database.signature, count
    finally:
        database.close()


def load_context(args: argparse.Namespace) -> barrage.BarrageContext:
    cases = matrix._read_yaml(args.cases)
    if int(cases.get("schema_version") or 0) != 2:
        raise ValueError("solver matrix cases must use schema_version: 2")
    model = json.loads(args.model.read_text(encoding="utf-8"))
    source_matrix_signature, config_count = _source_contract(args, model)
    fertilizers = load_fertilizers()
    molar_masses = load_molar_masses()
    profiles = tuple(matrix.load_target_profiles(cases, args.profiles))
    named_portfolios = matrix.load_fertilizer_portfolios(cases, fertilizers)
    available = {
        portfolio.portfolio_id: portfolio for portfolio in matrix.mass_barrage_portfolios(cases, named_portfolios)
    }
    portfolio_ids = tuple(item.strip() for item in args.portfolio_ids.split(",") if item.strip())
    missing = sorted(set(portfolio_ids) - set(available))
    if missing:
        raise ValueError(f"Unknown screening portfolios: {', '.join(missing)}")
    portfolios = tuple(available[portfolio_id] for portfolio_id in portfolio_ids)
    if not portfolios:
        raise ValueError("At least one screening portfolio is required")
    water_profile_name = args.water_profile or str(cases.get("water_profile") or "65936")
    osmosis_percent = float(args.osmosis_percent if args.osmosis_percent is not None else cases["osmosis_percent"])
    liters = float(args.liters if args.liters is not None else cases.get("liters") or 10.0)
    water_profile_data = dict(load_water_profile_data(resolve_water_profile_path(water_profile_name, ROOT)))
    water_profile_data["osmosis_percent"] = osmosis_percent
    element_order = exhaustive._element_order(profiles, water_profile_data)
    used_fertilizers = sorted({name for portfolio in portfolios for name in portfolio.fertilizers})
    source_sha256 = exhaustive._hash_files(
        (
            args.cases,
            ROOT / "scripts" / "solver_matrix.py",
            ROOT / "scripts" / "solver_preference_barrage.py",
            ROOT / "scripts" / "solver_preference_screen.py",
            ROOT / "src" / "horticalc" / "solver.py",
            ROOT / "src" / "horticalc" / "solver_config.py",
        )
    )
    contract = {
        "schema_version": SCHEMA_VERSION,
        "source_matrix_signature": source_matrix_signature,
        "source_config_count": config_count,
        "preference_model_sha256": hashlib.sha256(args.model.read_bytes()).hexdigest(),
        "source_sha256": source_sha256,
        "profiles": [asdict(profile) for profile in profiles],
        "portfolios": [asdict(portfolio) for portfolio in portfolios],
        "fertilizers": exhaustive._fertilizer_contract(fertilizers, used_fertilizers),
        "molar_masses": molar_masses,
        "water_profile_name": water_profile_name,
        "water_profile_data": water_profile_data,
        "osmosis_percent": osmosis_percent,
        "liters": liters,
        "element_order": element_order,
    }
    signature = barrage._sha256_json(contract)
    manifest = {
        **contract,
        "signature": signature,
        "planned_tasks": config_count * len(portfolios),
        "planned_solves": config_count * len(portfolios) * len(profiles),
        "storage": "normalized SQLite; exact achieved vectors deduplicated by SHA-256",
        "selection": "multi-view learned-cost screening before the full portfolio barrage",
    }
    return barrage.BarrageContext(
        profiles=profiles,
        portfolios=portfolios,
        configs=(),
        fertilizers=fertilizers,
        molar_masses=molar_masses,
        water_profile_name=water_profile_name,
        water_profile_data=water_profile_data,
        osmosis_percent=osmosis_percent,
        liters=liters,
        element_order=element_order,
        signature=signature,
        manifest=manifest,
    )


def _stored_analysis_inputs_match(connection: sqlite3.Connection, context: barrage.BarrageContext) -> bool:
    row = connection.execute("SELECT value FROM meta WHERE key = 'manifest'").fetchone()
    if row is None:
        return False
    stored = json.loads(row[0])
    keys = (
        "schema_version",
        "source_matrix_signature",
        "source_config_count",
        "profiles",
        "portfolios",
        "fertilizers",
        "molar_masses",
        "water_profile_name",
        "water_profile_data",
        "osmosis_percent",
        "liters",
        "element_order",
        "planned_solves",
    )
    return all(barrage._sha256_json(stored.get(key)) == barrage._sha256_json(context.manifest.get(key)) for key in keys)


def _screen_tasks(
    source_database: Path,
    connection: sqlite3.Connection,
    context: barrage.BarrageContext,
    completed: set[tuple[int, str]],
) -> Iterator[tuple[int, str, dict[str, Any], str]]:
    source = sqlite3.connect(f"file:{source_database.resolve().as_posix()}?mode=ro", uri=True)
    try:
        rows = source.execute(
            "SELECT config_id, config_hash, values_json FROM configs ORDER BY config_id LIMIT ?",
            (context.manifest["source_config_count"],),
        )
        for position, (config_id, config_hash, values_json) in enumerate(rows, start=1):
            config_id = int(config_id)
            values = json.loads(values_json)
            connection.execute(
                """
                INSERT OR IGNORE INTO configs(config_id, config_hash, values_json, varied_keys_json)
                VALUES (?, ?, ?, '[]')
                """,
                (config_id, str(config_hash), values_json),
            )
            if position % 10_000 == 0:
                connection.commit()
            for portfolio in context.portfolios:
                if (config_id, portfolio.portfolio_id) not in completed:
                    yield config_id, str(config_hash), values, portfolio.portfolio_id
        connection.commit()
    finally:
        source.close()


def run_screen(
    args: argparse.Namespace,
    context: barrage.BarrageContext,
    connection: sqlite3.Connection,
) -> dict[str, Any]:
    resumed = barrage.initialize_database(connection, context)
    completed_before = barrage._completed_tasks(connection, context)
    writer = barrage.BarrageWriter(connection, context)
    workers = args.workers or max(1, os.cpu_count() or 1)
    if workers < 1 or args.queue_depth < 1 or args.commit_every < 1:
        raise ValueError("workers, queue depth, and commit interval must be positive")
    started = time.perf_counter()
    executed = barrage._run_tasks(
        _screen_tasks(args.source_database, connection, context, completed_before),
        writer,
        barrage._worker_payload(context),
        workers=workers,
        queue_depth=args.queue_depth,
        commit_every=args.commit_every,
    )
    connection.commit()
    status_counts = dict(connection.execute("SELECT status, COUNT(*) FROM runs GROUP BY status").fetchall())
    total_runs = sum(int(value) for value in status_counts.values())
    errors = int(status_counts.get("error", 0))
    if total_runs != context.manifest["planned_solves"]:
        status = "partial"
    elif errors:
        status = "complete_with_errors"
    else:
        status = "complete"
    connection.execute("INSERT OR REPLACE INTO meta(key, value) VALUES ('status', ?)", (status,))
    connection.commit()
    summary = {
        "schema_version": SCHEMA_VERSION,
        "signature": context.signature,
        "database": str(args.database),
        "resumed": resumed,
        "workers": workers,
        "queue_depth": args.queue_depth,
        "config_count": context.manifest["source_config_count"],
        "profile_count": len(context.profiles),
        "portfolio_count": len(context.portfolios),
        "planned_solves": context.manifest["planned_solves"],
        "total_runs": total_runs,
        "status_counts": status_counts,
        "executed_tasks_this_invocation": executed,
        "elapsed_seconds": time.perf_counter() - started,
        "status": status,
    }
    (args.out_dir / "screening_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def _score_arrays(
    connection: sqlite3.Connection,
    context: barrage.BarrageContext,
    model: dict[str, Any],
) -> tuple[np.ndarray, list[tuple[str, str]], np.ndarray, np.ndarray]:
    config_ids = np.array(
        [int(row[0]) for row in connection.execute("SELECT config_id FROM configs ORDER BY config_id")],
        dtype=int,
    )
    config_index = {int(config_id): index for index, config_id in enumerate(config_ids)}
    cases = [
        (profile.profile_id, portfolio.portfolio_id) for profile in context.profiles for portfolio in context.portfolios
    ]
    case_index = {case: index for index, case in enumerate(cases)}
    element_costs = np.full((len(config_ids), len(cases)), np.inf, dtype=np.float32)
    total_costs = np.full((len(config_ids), len(cases)), np.inf, dtype=np.float32)
    names = tuple(model["features"])
    scales = np.array(model["scales"], dtype=float)
    weights = np.array(model["weights"], dtype=float)
    feature_elements = np.array([name.split(":", 1)[0] for name in names])
    element_index = {key: index for index, key in enumerate(context.element_order)}
    for profile in context.profiles:
        profile_id = profile.profile_id
        objective_row = connection.execute(
            "SELECT objective_elements_json FROM profiles WHERE profile_id = ?", (profile_id,)
        ).fetchone()
        elements = tuple(json.loads(objective_row[0]))
        targets = {key: float(profile.targets_mg_per_l.get(key, 0.0)) for key in elements}
        profile_context = (model.get("profile_contexts") or {}).get(profile_id)
        if not profile_context:
            raise ValueError(f"Preference model has no reachability context for {profile_id}")
        spans = profile_context["reachable_error_span_mg_per_l"]
        solution_rows = list(
            connection.execute(
                """
                SELECT DISTINCT r.solution_id, s.solution_hash, s.achieved_vector
                FROM runs AS r
                JOIN solutions AS s ON s.solution_id = r.solution_id
                WHERE r.profile_id = ? AND r.status = 'ok'
                """,
                (profile_id,),
            )
        )
        solutions = []
        for solution_id, solution_hash, payload in solution_rows:
            achieved = exhaustive._unpack_vector(payload, len(context.element_order))
            achieved_values = {key: float(achieved[element_index[key]]) for key in elements}
            solutions.append(
                {
                    "solution_id": int(solution_id),
                    "solution_hash": str(solution_hash),
                    "targets_mg_per_l": targets,
                    "achieved_mg_per_l": achieved_values,
                    "signed_errors_mg_per_l": {key: achieved_values[key] - targets[key] for key in elements},
                    "reachable_error_span_mg_per_l": spans,
                }
            )
        transformed = preference._transform_features(preference._feature_matrix(solutions, names), scales)
        contributions = transformed * weights
        solution_scores: dict[int, tuple[float, float]] = {}
        for row_index, solution in enumerate(solutions):
            by_element = [float(contributions[row_index, feature_elements == element].sum()) for element in elements]
            solution_scores[int(solution["solution_id"])] = (
                float(contributions[row_index].sum()),
                max(by_element),
            )
        for config_id, portfolio_id, solution_id in connection.execute(
            """
            SELECT config_id, portfolio_id, solution_id
            FROM runs WHERE profile_id = ? AND status = 'ok'
            """,
            (profile_id,),
        ):
            row = config_index[int(config_id)]
            column = case_index[(profile_id, str(portfolio_id))]
            total, worst = solution_scores[int(solution_id)]
            total_costs[row, column] = total
            element_costs[row, column] = worst
    if not np.isfinite(total_costs).all():
        raise ValueError("Screening database has missing or failed cases")
    return config_ids, cases, element_costs, total_costs


def analyze_screen(
    args: argparse.Namespace,
    connection: sqlite3.Connection,
    context: barrage.BarrageContext,
    model: dict[str, Any],
) -> dict[str, Any]:
    status = connection.execute("SELECT value FROM meta WHERE key = 'status'").fetchone()
    if status is None or status[0] != "complete":
        raise ValueError("Screening analysis requires a complete database")
    config_ids, cases, element_costs, total_costs = _score_arrays(connection, context, model)
    full_mask = np.ones(len(cases), dtype=bool)
    full_order, full_metrics = barrage._rank_metrics(config_ids, element_costs, total_costs, full_mask)
    full_ranks = barrage._competition_ranks(full_order, full_metrics)
    selected: dict[int, set[str]] = {}

    def add(reason: str, indices: np.ndarray) -> None:
        for index in indices:
            selected.setdefault(int(index), set()).add(reason)

    add("lexicographic", full_order[: args.lex_top])
    worst_case_order = np.lexsort((config_ids, full_metrics[2], full_metrics[1]))
    add("worst_case", worst_case_order[: args.worst_case_top])
    mean_order = np.lexsort((config_ids, full_metrics[2]))
    add("mean_case", mean_order[: args.mean_top])
    for portfolio in context.portfolios:
        mask = np.array([case[1] == portfolio.portfolio_id for case in cases])
        order, _ = barrage._rank_metrics(config_ids, element_costs, total_costs, mask)
        add(f"portfolio:{portfolio.portfolio_id}", order[: args.per_portfolio_top])
    for profile in context.profiles:
        mask = np.array([case[0] == profile.profile_id for case in cases])
        order, _ = barrage._rank_metrics(config_ids, element_costs, total_costs, mask)
        add(f"profile:{profile.profile_id}", order[: args.per_profile_top])
        holdout_mask = ~mask
        if np.any(holdout_mask):
            order, _ = barrage._rank_metrics(config_ids, element_costs, total_costs, holdout_mask)
            add(f"profile_holdout:{profile.profile_id}", order[: args.per_profile_holdout_top])
    if len(context.portfolios) > 1:
        for portfolio in context.portfolios:
            holdout_mask = np.array([case[1] != portfolio.portfolio_id for case in cases])
            order, _ = barrage._rank_metrics(config_ids, element_costs, total_costs, holdout_mask)
            add(f"portfolio_holdout:{portfolio.portfolio_id}", order[: args.per_portfolio_holdout_top])
    config_index = {int(config_id): index for index, config_id in enumerate(config_ids)}
    for config_id in preference.REFERENCE_CONFIG_IDS:
        if config_id in config_index:
            selected.setdefault(config_index[config_id], set()).add("historical_reference")
    for included_path in args.include_ranking:
        included = json.loads(included_path.read_text(encoding="utf-8"))
        if str(included["matrix_signature"]) != context.manifest["source_matrix_signature"]:
            raise ValueError(f"Included ranking has a different matrix signature: {included_path}")
        for row in included["ranking"]:
            config_id = int(row["config_id"])
            if config_id not in config_index:
                raise ValueError(f"Included ranking contains unknown config {config_id}: {included_path}")
            selected.setdefault(config_index[config_id], set()).add(f"included:{included_path.name}")
    selected_indices = sorted(selected, key=lambda index: (int(full_ranks[index]), int(config_ids[index])))
    selected_ids = {int(config_ids[index]) for index in selected_indices}
    configs = {
        int(config_id): {
            "config_id": int(config_id),
            "config_hash": str(config_hash),
            "solver_config": json.loads(values_json),
        }
        for config_id, config_hash, values_json in connection.execute(
            "SELECT config_id, config_hash, values_json FROM configs"
        )
        if int(config_id) in selected_ids
    }
    ranking = []
    for index in selected_indices:
        config_id = int(config_ids[index])
        ranking.append(
            {
                **configs[config_id],
                "rank": int(full_ranks[index]),
                "screening_worst_element_cost": float(full_metrics[0][index]),
                "screening_worst_case_cost": float(full_metrics[1][index]),
                "screening_mean_case_cost": float(full_metrics[2][index]),
                "selection_reasons": sorted(selected[index]),
            }
        )
    references = {
        str(config_id): {
            "rank": int(full_ranks[config_index[config_id]]),
            **configs[config_id],
        }
        for config_id in preference.REFERENCE_CONFIG_IDS
        if config_id in configs
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "matrix_signature": context.manifest["source_matrix_signature"],
        "screening_signature": context.signature,
        "selection": (
            "union of learned-cost lexicographic, worst-case, mean, per-profile, "
            "per-portfolio, profile/portfolio-holdout, and historical-reference leaders"
        ),
        "screened_configurations": len(config_ids),
        "screening_case_count": len(cases),
        "analysis_model_sha256": hashlib.sha256(
            json.dumps(model, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
        "analysis_feature_structure": model.get("feature_structure", "independent"),
        "selected_configurations": len(ranking),
        "references": references,
        "ranking": ranking,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Screen every exhaustive solver setting on discriminating stress portfolios."
    )
    parser.add_argument("--cases", type=Path, default=matrix.DEFAULT_CASES_PATH)
    parser.add_argument("--source-database", type=Path, default=preference.DEFAULT_DATABASE)
    parser.add_argument("--model", type=Path, default=preference.DEFAULT_MODEL_PATH)
    parser.add_argument("--analysis-model", type=Path, default=None)
    parser.add_argument("--analysis-out", type=Path, default=None)
    parser.add_argument("--include-ranking", type=Path, action="append", default=[])
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--database", type=Path, default=None)
    parser.add_argument("--portfolio-ids", default=",".join(DEFAULT_PORTFOLIO_IDS))
    parser.add_argument("--profiles", default="all")
    parser.add_argument("--water-profile", default=None)
    parser.add_argument("--osmosis-percent", type=float, default=None)
    parser.add_argument("--liters", type=float, default=None)
    parser.add_argument("--max-configs", type=int, default=None)
    parser.add_argument("--workers", type=int, default=24)
    parser.add_argument("--queue-depth", type=int, default=10_000)
    parser.add_argument("--commit-every", type=int, default=100)
    parser.add_argument("--lex-top", type=int, default=10_000)
    parser.add_argument("--worst-case-top", type=int, default=5_000)
    parser.add_argument("--mean-top", type=int, default=5_000)
    parser.add_argument("--per-portfolio-top", type=int, default=2_000)
    parser.add_argument("--per-profile-top", type=int, default=1_000)
    parser.add_argument("--per-portfolio-holdout-top", type=int, default=2_000)
    parser.add_argument("--per-profile-holdout-top", type=int, default=2_000)
    parser.add_argument("--analyze-only", action="store_true")
    parser.add_argument("--skip-analysis", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    positive = (
        args.lex_top,
        args.worst_case_top,
        args.mean_top,
        args.per_portfolio_top,
        args.per_profile_top,
        args.per_portfolio_holdout_top,
        args.per_profile_holdout_top,
    )
    if any(value < 1 for value in positive):
        raise ValueError("All shortlist selector counts must be positive")
    if args.max_configs is not None and args.max_configs < 1:
        raise ValueError("--max-configs must be positive")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    if args.database is None:
        args.database = args.out_dir / "preference_screen.sqlite3"
    context = load_context(args)
    connection = exhaustive.open_database(args.database)
    try:
        if args.analyze_only:
            existing = connection.execute("SELECT value FROM meta WHERE key = 'signature'").fetchone()
            if existing is None or (
                existing[0] != context.signature and not _stored_analysis_inputs_match(connection, context)
            ):
                raise ValueError("Screen database does not match the requested analysis inputs")
        else:
            summary = run_screen(args, context, connection)
            print(
                f"Screen {summary['status']}: {summary['total_runs']:,}/"
                f"{summary['planned_solves']:,} solves in {summary['elapsed_seconds']:.2f}s"
            )
        if not args.skip_analysis:
            analysis_model_path = args.analysis_model or args.model
            model = json.loads(analysis_model_path.read_text(encoding="utf-8"))
            if str(model["matrix_signature"]) != context.manifest["source_matrix_signature"]:
                raise ValueError("Analysis model and stored solver matrix signatures differ")
            analysis = analyze_screen(args, connection, context, model)
            output = args.analysis_out or (args.out_dir / "screening_ranking.json")
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(
                json.dumps(analysis, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            print(
                f"Selected {analysis['selected_configurations']:,} of "
                f"{analysis['screened_configurations']:,} configurations"
            )
    finally:
        connection.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
