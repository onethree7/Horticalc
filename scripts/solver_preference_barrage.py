from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import sys
import time
from collections import OrderedDict
from concurrent.futures import FIRST_COMPLETED, Future, ProcessPoolExecutor, wait
from contextlib import suppress
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator

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
from horticalc.data_io import (  # noqa: E402
    Fertilizer,
    load_fertilizers,
    load_molar_masses,
    load_water_profile_data,
)
from horticalc.paths import logs_dir, resolve_water_profile_path  # noqa: E402

SCHEMA_VERSION = 1
DEFAULT_OUT_DIR = logs_dir(ROOT) / "solver_matrix" / "preference_barrage"


@dataclass(frozen=True)
class ShortlistConfig:
    config_id: int
    config_hash: str
    values: dict[str, Any]


@dataclass(frozen=True)
class BarrageContext:
    profiles: tuple[matrix.TargetProfile, ...]
    portfolios: tuple[matrix.FertilizerPortfolio, ...]
    configs: tuple[ShortlistConfig, ...]
    fertilizers: dict[str, Fertilizer]
    molar_masses: dict[str, float]
    water_profile_name: str
    water_profile_data: dict[str, Any]
    osmosis_percent: float
    liters: float
    element_order: tuple[str, ...]
    signature: str
    manifest: dict[str, Any]


@dataclass(frozen=True)
class PortfolioBatchResult:
    config_id: int
    portfolio_id: str
    runs: tuple[exhaustive.CompactRun, ...]


_WORKER_STATE: dict[str, Any] = {}


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(_json(value).encode("utf-8")).hexdigest()


def _load_shortlist(path: Path, top: int) -> tuple[str, tuple[ShortlistConfig, ...]]:
    ranking = json.loads(path.read_text(encoding="utf-8"))
    rows = list(ranking.get("ranking") or [])[:top]
    if not rows:
        raise ValueError("Preference ranking contains no configurations")
    configs = tuple(
        ShortlistConfig(
            config_id=int(row["config_id"]),
            config_hash=str(row["config_hash"]),
            values=dict(row["solver_config"]),
        )
        for row in rows
    )
    if len({config.config_id for config in configs}) != len(configs):
        raise ValueError("Preference shortlist contains duplicate configuration ids")
    return str(ranking["matrix_signature"]), configs


def load_context(args: argparse.Namespace) -> BarrageContext:
    cases = matrix._read_yaml(args.cases)
    if int(cases.get("schema_version") or 0) != 2:
        raise ValueError("solver matrix cases must use schema_version: 2")
    source_matrix_signature, configs = _load_shortlist(args.ranking, args.top)
    model = json.loads(args.model.read_text(encoding="utf-8"))
    if str(model["matrix_signature"]) != source_matrix_signature:
        raise ValueError("Preference model and ranking matrix signatures differ")
    fertilizers = load_fertilizers()
    molar_masses = load_molar_masses()
    profiles = tuple(matrix.load_target_profiles(cases, args.profiles))
    named_portfolios = matrix.load_fertilizer_portfolios(cases, fertilizers)
    portfolios = tuple(matrix.mass_barrage_portfolios(cases, named_portfolios))
    if not portfolios:
        raise ValueError("The cases file defines no mass-barrage portfolios")
    if len({portfolio.portfolio_id for portfolio in portfolios}) != len(portfolios):
        raise ValueError("Mass-barrage portfolio ids must be unique")
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
            ROOT / "src" / "horticalc" / "solver.py",
            ROOT / "src" / "horticalc" / "solver_config.py",
        )
    )
    contract = {
        "schema_version": SCHEMA_VERSION,
        "source_matrix_signature": source_matrix_signature,
        "preference_model_sha256": hashlib.sha256(args.model.read_bytes()).hexdigest(),
        "source_sha256": source_sha256,
        "shortlist": [asdict(config) for config in configs],
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
    signature = _sha256_json(contract)
    manifest = {
        **contract,
        "signature": signature,
        "planned_tasks": len(configs) * len(portfolios),
        "planned_solves": len(configs) * len(portfolios) * len(profiles),
        "storage": "normalized SQLite; exact achieved vectors deduplicated by SHA-256",
        "selection": (
            "lexicographic worst learned element penalty, worst case, then mean; "
            "profile and portfolio holdouts plus deterministic bootstrap"
        ),
    }
    return BarrageContext(
        profiles=profiles,
        portfolios=portfolios,
        configs=configs,
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


def _worker_initializer(payload: dict[str, Any]) -> None:
    _WORKER_STATE.clear()
    _WORKER_STATE.update(payload)


def _worker_payload(context: BarrageContext) -> dict[str, Any]:
    return {
        "profiles": context.profiles,
        "portfolios": {portfolio.portfolio_id: portfolio for portfolio in context.portfolios},
        "fertilizers": context.fertilizers,
        "molar_masses": context.molar_masses,
        "water_profile_name": context.water_profile_name,
        "water_profile_data": context.water_profile_data,
        "osmosis_percent": context.osmosis_percent,
        "liters": context.liters,
        "element_order": context.element_order,
    }


def _execute_task(task: tuple[int, str, dict[str, Any], str]) -> PortfolioBatchResult:
    config_id, config_hash, values, portfolio_id = task
    state = _WORKER_STATE
    portfolio = state["portfolios"][portfolio_id]
    config = matrix.SolverConfigCase(
        experiment_id="preference_barrage",
        config_id=config_hash,
        name=f"preference-barrage:{config_hash[:16]}",
        values=values,
        varied_keys=(),
    )
    runs = []
    for profile in state["profiles"]:
        row = matrix.solve_case(
            profile=profile,
            portfolio=portfolio,
            config=config,
            preset="preference_barrage",
            phase="mass_barrage",
            liters=state["liters"],
            water_profile_name=state["water_profile_name"],
            osmosis_percent=state["osmosis_percent"],
            water_profile_data=state["water_profile_data"],
            fertilizers=state["fertilizers"],
            molar_masses=state["molar_masses"],
        )
        runs.append(exhaustive._compact_row(row, state["element_order"]))
    return PortfolioBatchResult(
        config_id=config_id,
        portfolio_id=portfolio_id,
        runs=tuple(runs),
    )


def initialize_database(
    connection: sqlite3.Connection,
    context: BarrageContext,
) -> bool:
    existing = connection.execute("SELECT value FROM meta WHERE key = 'signature'").fetchone()
    if existing is not None and existing[0] != context.signature:
        raise ValueError("Existing barrage database has different inputs; use a new output directory")
    resumed = existing is not None
    metadata = {
        "schema_version": str(SCHEMA_VERSION),
        "signature": context.signature,
        "manifest": _json(context.manifest),
        "status": "running",
    }
    connection.executemany("INSERT OR REPLACE INTO meta(key, value) VALUES (?, ?)", metadata.items())
    for ordinal, profile in enumerate(context.profiles):
        connection.execute(
            """
            INSERT OR IGNORE INTO profiles(
                profile_id, ordinal, name, group_name, source, targets_json, target_vector
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                profile.profile_id,
                ordinal,
                profile.name,
                profile.group,
                profile.source,
                _json(profile.targets_mg_per_l),
                exhaustive._mapping_vector(profile.targets_mg_per_l, context.element_order),
            ),
        )
    for portfolio in context.portfolios:
        connection.execute(
            "INSERT OR IGNORE INTO portfolios(portfolio_id, source, fertilizers_json) VALUES (?, ?, ?)",
            (portfolio.portfolio_id, portfolio.source, _json(portfolio.fertilizers)),
        )
    for config in context.configs:
        connection.execute(
            """
            INSERT OR IGNORE INTO configs(config_id, config_hash, values_json, varied_keys_json)
            VALUES (?, ?, ?, '[]')
            """,
            (config.config_id, config.config_hash, _json(config.values)),
        )
    connection.commit()
    return resumed


def _completed_tasks(connection: sqlite3.Connection, context: BarrageContext) -> set[tuple[int, str]]:
    rows = connection.execute(
        """
        SELECT config_id, portfolio_id
        FROM runs
        GROUP BY config_id, portfolio_id
        HAVING COUNT(DISTINCT profile_id) = ?
        """,
        (len(context.profiles),),
    )
    return {(int(config_id), str(portfolio_id)) for config_id, portfolio_id in rows}


def _tasks(
    context: BarrageContext,
    completed: set[tuple[int, str]],
) -> Iterator[tuple[int, str, dict[str, Any], str]]:
    for config in context.configs:
        for portfolio in context.portfolios:
            key = (config.config_id, portfolio.portfolio_id)
            if key not in completed:
                yield config.config_id, config.config_hash, config.values, portfolio.portfolio_id


class BarrageWriter:
    def __init__(self, connection: sqlite3.Connection, context: BarrageContext) -> None:
        self.connection = connection
        self.context = context
        self.solution_cache: OrderedDict[str, int] = OrderedDict()
        self.objectives = {
            str(profile_id): (tuple(json.loads(payload)) if payload else None)
            for profile_id, payload in connection.execute("SELECT profile_id, objective_elements_json FROM profiles")
        }

    def _solution_id(self, result: exhaustive.CompactRun) -> int | None:
        if result.solution_hash is None or result.achieved_vector is None:
            return None
        cached = self.solution_cache.get(result.solution_hash)
        if cached is not None:
            self.solution_cache.move_to_end(result.solution_hash)
            return cached
        inserted = self.connection.execute(
            """
            INSERT INTO solutions(solution_hash, achieved_vector)
            VALUES (?, ?)
            ON CONFLICT(solution_hash) DO NOTHING
            RETURNING solution_id
            """,
            (result.solution_hash, result.achieved_vector),
        ).fetchone()
        if inserted:
            solution_id = int(inserted[0])
        else:
            solution_id = int(
                self.connection.execute(
                    "SELECT solution_id FROM solutions WHERE solution_hash = ?",
                    (result.solution_hash,),
                ).fetchone()[0]
            )
        self.solution_cache[result.solution_hash] = solution_id
        if len(self.solution_cache) > 100_000:
            self.solution_cache.popitem(last=False)
        return solution_id

    def _record_objectives(self, result: exhaustive.CompactRun) -> None:
        if not result.objective_elements:
            return
        normalized = tuple(key for key in self.context.element_order if key in result.objective_elements)
        existing = self.objectives[result.profile_id]
        if existing is None:
            self.connection.execute(
                "UPDATE profiles SET objective_elements_json = ? WHERE profile_id = ?",
                (_json(normalized), result.profile_id),
            )
            self.objectives[result.profile_id] = normalized
        elif existing != normalized:
            raise ValueError(f"Objective elements changed within profile {result.profile_id}")

    def write(self, batch: PortfolioBatchResult) -> None:
        for result in batch.runs:
            self._record_objectives(result)
            solution_id = self._solution_id(result)
            self.connection.execute(
                """
                INSERT OR IGNORE INTO runs(
                    config_id, profile_id, portfolio_id, solution_id, status,
                    elapsed_seconds, legacy_composite_score, legacy_macro_score,
                    legacy_n_form_score, legacy_micro_score, legacy_other_score,
                    legacy_ignored_score, total_grams, used_fertilizer_count, error
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    batch.config_id,
                    result.profile_id,
                    batch.portfolio_id,
                    solution_id,
                    result.status,
                    result.elapsed_seconds,
                    result.legacy_composite_score,
                    result.legacy_macro_score,
                    result.legacy_n_form_score,
                    result.legacy_micro_score,
                    result.legacy_other_score,
                    result.legacy_ignored_score,
                    result.total_grams,
                    result.used_fertilizer_count,
                    result.error,
                ),
            )


def _run_tasks(
    tasks: Iterable[tuple[int, str, dict[str, Any], str]],
    writer: BarrageWriter,
    payload: dict[str, Any],
    *,
    workers: int,
    queue_depth: int,
    commit_every: int,
) -> int:
    if workers == 1:
        _worker_initializer(payload)
        completed = 0
        for task in tasks:
            writer.write(_execute_task(task))
            completed += 1
            if completed % commit_every == 0:
                writer.connection.commit()
        return completed
    iterator = iter(tasks)
    pending: set[Future[PortfolioBatchResult]] = set()
    completed = 0
    with ProcessPoolExecutor(
        max_workers=workers,
        initializer=_worker_initializer,
        initargs=(payload,),
    ) as executor:
        for _ in range(queue_depth):
            with suppress(StopIteration):
                pending.add(executor.submit(_execute_task, next(iterator)))
        while pending:
            done, pending = wait(pending, return_when=FIRST_COMPLETED)
            for future in done:
                writer.write(future.result())
                completed += 1
                if completed % commit_every == 0:
                    writer.connection.commit()
                with suppress(StopIteration):
                    pending.add(executor.submit(_execute_task, next(iterator)))
    return completed


def run_barrage(
    args: argparse.Namespace,
    context: BarrageContext,
    connection: sqlite3.Connection,
) -> dict[str, Any]:
    resumed = initialize_database(connection, context)
    completed_before = _completed_tasks(connection, context)
    writer = BarrageWriter(connection, context)
    workers = args.workers or max(1, os.cpu_count() or 1)
    if workers < 1 or args.queue_depth < 1 or args.commit_every < 1:
        raise ValueError("workers, queue depth, and commit interval must be positive")
    started = time.perf_counter()
    executed = _run_tasks(
        _tasks(context, completed_before),
        writer,
        _worker_payload(context),
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
        "config_count": len(context.configs),
        "profile_count": len(context.profiles),
        "portfolio_count": len(context.portfolios),
        "planned_solves": context.manifest["planned_solves"],
        "total_runs": total_runs,
        "status_counts": status_counts,
        "executed_tasks_this_invocation": executed,
        "elapsed_seconds": time.perf_counter() - started,
        "status": status,
    }
    (args.out_dir / "barrage_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def _rank_order(
    config_ids: np.ndarray,
    element_costs: np.ndarray,
    total_costs: np.ndarray,
    mask: np.ndarray,
) -> np.ndarray:
    worst_element = element_costs[:, mask].max(axis=1)
    worst_case = total_costs[:, mask].max(axis=1)
    mean_case = total_costs[:, mask].mean(axis=1)
    return np.lexsort((config_ids, mean_case, worst_case, worst_element))


def analyze_barrage(
    connection: sqlite3.Connection,
    context: BarrageContext,
    model: dict[str, Any],
    *,
    bootstrap_samples: int,
    seed: int,
) -> dict[str, Any]:
    if connection.execute("SELECT value FROM meta WHERE key = 'status'").fetchone()[0] != "complete":
        raise ValueError("Barrage analysis requires a complete database")
    config_ids = np.array([config.config_id for config in context.configs], dtype=int)
    config_index = {int(config_id): index for index, config_id in enumerate(config_ids)}
    cases = [
        (profile.profile_id, portfolio.portfolio_id) for profile in context.profiles for portfolio in context.portfolios
    ]
    case_index = {case: index for index, case in enumerate(cases)}
    element_costs = np.full((len(config_ids), len(cases)), np.inf, dtype=float)
    total_costs = np.full((len(config_ids), len(cases)), np.inf, dtype=float)
    worst_elements = np.empty((len(config_ids), len(cases)), dtype=object)
    names = tuple(model["features"])
    scales = np.array(model["scales"], dtype=float)
    weights = np.array(model["weights"], dtype=float)
    feature_elements = np.array([name.split(":", 1)[0] for name in names])
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
            achieved_values = {key: float(achieved[context.element_order.index(key)]) for key in elements}
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
        solution_scores: dict[int, tuple[float, float, str]] = {}
        for row_index, solution in enumerate(solutions):
            by_element = {
                element: float(contributions[row_index, feature_elements == element].sum()) for element in elements
            }
            worst_name, worst_value = max(by_element.items(), key=lambda item: (item[1], item[0]))
            solution_scores[int(solution["solution_id"])] = (
                float(contributions[row_index].sum()),
                worst_value,
                worst_name,
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
            total, worst, element = solution_scores[int(solution_id)]
            total_costs[row, column] = total
            element_costs[row, column] = worst
            worst_elements[row, column] = element
    if not np.isfinite(total_costs).all():
        raise ValueError("Barrage database has missing or failed cases")
    full_mask = np.ones(len(cases), dtype=bool)
    order = _rank_order(config_ids, element_costs, total_costs, full_mask)
    profile_holdouts = {}
    for profile in context.profiles:
        mask = np.array([case[0] != profile.profile_id for case in cases])
        if np.any(mask):
            holdout_order = _rank_order(config_ids, element_costs, total_costs, mask)
            profile_holdouts[profile.profile_id] = {
                str(int(config_ids[index])): rank for rank, index in enumerate(holdout_order, start=1)
            }
    portfolio_holdouts = {}
    for portfolio in context.portfolios:
        mask = np.array([case[1] != portfolio.portfolio_id for case in cases])
        holdout_order = _rank_order(config_ids, element_costs, total_costs, mask)
        portfolio_holdouts[portfolio.portfolio_id] = {
            str(int(config_ids[index])): rank for rank, index in enumerate(holdout_order, start=1)
        }
    rng = np.random.default_rng(seed)
    bootstrap_ranks = np.empty((bootstrap_samples, len(config_ids)), dtype=np.int32)
    for sample_index in range(bootstrap_samples):
        sampled = rng.integers(0, len(cases), size=len(cases))
        sample_order = _rank_order(
            config_ids,
            element_costs[:, sampled],
            total_costs[:, sampled],
            np.ones(len(sampled), dtype=bool),
        )
        bootstrap_ranks[sample_index, sample_order] = np.arange(1, len(config_ids) + 1)
    rows = []
    for rank, index in enumerate(order, start=1):
        config_id = int(config_ids[index])
        worst_column = int(np.argmax(element_costs[index]))
        worst_case_column = int(np.argmax(total_costs[index]))
        profile_means = {
            profile.profile_id: float(total_costs[index, [case[0] == profile.profile_id for case in cases]].mean())
            for profile in context.profiles
        }
        worst_profile_id = max(profile_means, key=profile_means.get)
        config = next(item for item in context.configs if item.config_id == config_id)
        sampled_ranks = bootstrap_ranks[:, index]
        rows.append(
            {
                "rank": rank,
                "config_id": config_id,
                "config_hash": config.config_hash,
                "solver_config": config.values,
                "worst_element_cost": float(element_costs[index, worst_column]),
                "worst_element": {
                    "profile_id": cases[worst_column][0],
                    "portfolio_id": cases[worst_column][1],
                    "element": str(worst_elements[index, worst_column]),
                },
                "worst_case_cost": float(total_costs[index, worst_case_column]),
                "worst_case": {
                    "profile_id": cases[worst_case_column][0],
                    "portfolio_id": cases[worst_case_column][1],
                },
                "mean_case_cost": float(total_costs[index].mean()),
                "worst_profile": {
                    "profile_id": worst_profile_id,
                    "mean_cost": profile_means[worst_profile_id],
                },
                "leave_one_profile_out_ranks": {
                    profile_id: ranks[str(config_id)] for profile_id, ranks in profile_holdouts.items()
                },
                "leave_one_portfolio_out_ranks": {
                    portfolio_id: ranks[str(config_id)] for portfolio_id, ranks in portfolio_holdouts.items()
                },
                "bootstrap": {
                    "median_rank": float(np.median(sampled_ranks)),
                    "rank_p90": float(np.quantile(sampled_ranks, 0.9)),
                    "top_10_share": float(np.mean(sampled_ranks <= 10)),
                    "win_share": float(np.mean(sampled_ranks == 1)),
                },
            }
        )
    winner_margin = None
    if len(order) > 1:
        first, second = int(order[0]), int(order[1])
        winner_margin = {
            "worst_element_cost": float(element_costs[second].max() - element_costs[first].max()),
            "worst_case_cost": float(total_costs[second].max() - total_costs[first].max()),
            "mean_case_cost": float(total_costs[second].mean() - total_costs[first].mean()),
        }
    return {
        "schema_version": SCHEMA_VERSION,
        "barrage_signature": context.signature,
        "source_matrix_signature": context.manifest["source_matrix_signature"],
        "selection": context.manifest["selection"],
        "case_count": len(cases),
        "config_count": len(config_ids),
        "bootstrap_samples": bootstrap_samples,
        "winner_margin_to_second": winner_margin,
        "ranking": rows,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate learned solver preferences across the nutrient portfolio barrage."
    )
    parser.add_argument("--cases", type=Path, default=matrix.DEFAULT_CASES_PATH)
    parser.add_argument("--ranking", type=Path, default=preference.DEFAULT_RANKING_PATH)
    parser.add_argument("--model", type=Path, default=preference.DEFAULT_MODEL_PATH)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--database", type=Path, default=None)
    parser.add_argument("--top", type=int, default=200)
    parser.add_argument("--profiles", default="all", help="all configured cases, or comma-separated profile ids")
    parser.add_argument("--water-profile", default=None)
    parser.add_argument("--osmosis-percent", type=float, default=None)
    parser.add_argument("--liters", type=float, default=None)
    parser.add_argument("--workers", type=int, default=24)
    parser.add_argument("--queue-depth", type=int, default=10_000)
    parser.add_argument("--commit-every", type=int, default=100)
    parser.add_argument("--bootstrap-samples", type=int, default=500)
    parser.add_argument("--seed", type=int, default=20260716)
    parser.add_argument("--analyze-only", action="store_true")
    parser.add_argument("--skip-analysis", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.top < 1 or args.bootstrap_samples < 1:
        raise ValueError("--top and --bootstrap-samples must be positive")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    if args.database is None:
        args.database = args.out_dir / "preference_barrage.sqlite3"
    context = load_context(args)
    connection = exhaustive.open_database(args.database)
    try:
        if args.analyze_only:
            existing = connection.execute("SELECT value FROM meta WHERE key = 'signature'").fetchone()
            if existing is None or existing[0] != context.signature:
                raise ValueError("Barrage database does not match the requested analysis inputs")
        else:
            summary = run_barrage(args, context, connection)
            print(
                f"Barrage {summary['status']}: {summary['total_runs']:,}/"
                f"{summary['planned_solves']:,} solves in {summary['elapsed_seconds']:.2f}s"
            )
        if not args.skip_analysis:
            model = json.loads(args.model.read_text(encoding="utf-8"))
            analysis = analyze_barrage(
                connection,
                context,
                model,
                bootstrap_samples=args.bootstrap_samples,
                seed=args.seed,
            )
            output = args.out_dir / "barrage_ranking.json"
            output.write_text(
                json.dumps(analysis, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            print(
                f"Barrage winner: config {analysis['ranking'][0]['config_id']} "
                f"({analysis['case_count']} profile-portfolio cases)"
            )
    finally:
        connection.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
