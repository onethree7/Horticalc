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
    selected_ids = {int(row["config_id"]) for row in rows}
    for reference in (ranking.get("references") or {}).values():
        reference_id = int(reference["config_id"])
        if reference_id not in selected_ids:
            rows.append(reference)
            selected_ids.add(reference_id)
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


def _shortlist_hash(configs: tuple[ShortlistConfig, ...]) -> str:
    return _sha256_json([asdict(config) for config in configs])


def _stored_analysis_inputs_match(connection: sqlite3.Connection, context: BarrageContext) -> bool:
    row = connection.execute("SELECT value FROM meta WHERE key = 'manifest'").fetchone()
    if row is None:
        return False
    stored = json.loads(row[0])
    # Execution/resume must match code and model hashes. Rescoring consumes only
    # stored achieved vectors, so it instead requires identical semantic cases,
    # vector layout, and configuration identities.
    keys = (
        "schema_version",
        "source_matrix_signature",
        "shortlist_config_count",
        "shortlist_sha256",
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
    return all(_sha256_json(stored.get(key)) == _sha256_json(context.manifest.get(key)) for key in keys)


def _stored_extension_inputs_match(connection: sqlite3.Connection, context: BarrageContext) -> bool:
    row = connection.execute("SELECT value FROM meta WHERE key = 'manifest'").fetchone()
    if row is None:
        return False
    stored = json.loads(row[0])
    keys = (
        "schema_version",
        "source_matrix_signature",
        "profiles",
        "portfolios",
        "fertilizers",
        "molar_masses",
        "water_profile_name",
        "water_profile_data",
        "osmosis_percent",
        "liters",
        "element_order",
    )
    if not all(_sha256_json(stored.get(key)) == _sha256_json(context.manifest.get(key)) for key in keys):
        return False
    current = {config.config_id: config for config in context.configs}
    for config_id, config_hash, values_json in connection.execute(
        "SELECT config_id, config_hash, values_json FROM configs"
    ):
        config = current.get(int(config_id))
        if config is None or config.config_hash != str(config_hash):
            return False
        if _sha256_json(config.values) != _sha256_json(json.loads(values_json)):
            return False
    return True


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
        "shortlist_config_count": len(configs),
        "shortlist_sha256": _shortlist_hash(configs),
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
    *,
    allow_shortlist_extension: bool = False,
) -> bool:
    existing = connection.execute("SELECT value FROM meta WHERE key = 'signature'").fetchone()
    if (
        existing is not None
        and existing[0] != context.signature
        and (not allow_shortlist_extension or not _stored_extension_inputs_match(connection, context))
    ):
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
    resumed = initialize_database(
        connection,
        context,
        allow_shortlist_extension=args.extend_shortlist,
    )
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


def _rank_metrics(
    config_ids: np.ndarray,
    element_costs: np.ndarray,
    total_costs: np.ndarray,
    mask: np.ndarray,
) -> tuple[np.ndarray, tuple[np.ndarray, np.ndarray, np.ndarray]]:
    worst_element = element_costs[:, mask].max(axis=1)
    worst_case = total_costs[:, mask].max(axis=1)
    mean_case = total_costs[:, mask].mean(axis=1)
    order = np.lexsort((config_ids, mean_case, worst_case, worst_element))
    return order, (worst_element, worst_case, mean_case)


def _score_key(metrics: tuple[np.ndarray, ...], index: int) -> tuple[float, ...]:
    return tuple(round(float(metric[index]), 12) for metric in metrics)


def _competition_ranks(order: np.ndarray, metrics: tuple[np.ndarray, ...]) -> np.ndarray:
    ranks = np.empty(len(order), dtype=np.int32)
    previous: tuple[float, ...] | None = None
    shared_rank = 0
    for position, index in enumerate(order, start=1):
        key = _score_key(metrics, int(index))
        if key != previous:
            shared_rank = position
            previous = key
        ranks[int(index)] = shared_rank
    return ranks


def _rank_map(
    config_ids: np.ndarray,
    element_costs: np.ndarray,
    total_costs: np.ndarray,
    mask: np.ndarray,
) -> dict[str, int]:
    order, metrics = _rank_metrics(config_ids, element_costs, total_costs, mask)
    ranks = _competition_ranks(order, metrics)
    return {str(int(config_id)): int(ranks[index]) for index, config_id in enumerate(config_ids)}


def _collapsed_ranks(
    config_ids: np.ndarray,
    element_costs: np.ndarray,
    total_costs: np.ndarray,
    mask: np.ndarray,
    representatives: np.ndarray,
    behavior_index: np.ndarray,
) -> tuple[np.ndarray, tuple[np.ndarray, np.ndarray, np.ndarray]]:
    representative_order, representative_metrics = _rank_metrics(
        config_ids[representatives],
        element_costs[representatives],
        total_costs[representatives],
        mask,
    )
    representative_ranks = _competition_ranks(representative_order, representative_metrics)
    all_metrics = (
        element_costs[:, mask].max(axis=1),
        total_costs[:, mask].max(axis=1),
        total_costs[:, mask].mean(axis=1),
    )
    return representative_ranks[behavior_index], all_metrics


def _collapsed_rank_map(
    config_ids: np.ndarray,
    element_costs: np.ndarray,
    total_costs: np.ndarray,
    mask: np.ndarray,
    representatives: np.ndarray,
    behavior_index: np.ndarray,
) -> dict[str, int]:
    ranks, _ = _collapsed_ranks(
        config_ids,
        element_costs,
        total_costs,
        mask,
        representatives,
        behavior_index,
    )
    return {str(int(config_id)): int(ranks[index]) for index, config_id in enumerate(config_ids)}


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
    solution_ids = np.full((len(config_ids), len(cases)), -1, dtype=np.int64)
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
            solution_ids[row, column] = int(solution_id)
    if not np.isfinite(total_costs).all():
        raise ValueError("Barrage database has missing or failed cases")
    behavior_groups: dict[str, list[int]] = {}
    behavior_hashes = []
    behavior_members: dict[str, list[int]] = {}
    for index, config_id in enumerate(config_ids):
        digest = hashlib.sha256(solution_ids[index].tobytes()).hexdigest()
        behavior_hashes.append(digest)
        behavior_groups.setdefault(digest, []).append(int(config_id))
        behavior_members.setdefault(digest, []).append(index)
    representative_hashes = sorted(behavior_members, key=lambda digest: min(behavior_groups[digest]))
    representatives = np.array(
        [min(behavior_members[digest], key=lambda index: int(config_ids[index])) for digest in representative_hashes],
        dtype=int,
    )
    representative_position = {digest: position for position, digest in enumerate(representative_hashes)}
    behavior_index = np.array([representative_position[digest] for digest in behavior_hashes], dtype=int)
    full_mask = np.ones(len(cases), dtype=bool)
    full_ranks, full_metrics = _collapsed_ranks(
        config_ids,
        element_costs,
        total_costs,
        full_mask,
        representatives,
        behavior_index,
    )
    order = np.lexsort((config_ids, full_metrics[2], full_metrics[1], full_metrics[0], full_ranks))
    profile_holdouts = {}
    for profile in context.profiles:
        mask = np.array([case[0] != profile.profile_id for case in cases])
        if np.any(mask):
            profile_holdouts[profile.profile_id] = _collapsed_rank_map(
                config_ids, element_costs, total_costs, mask, representatives, behavior_index
            )
    portfolio_holdouts = {}
    for portfolio in context.portfolios:
        mask = np.array([case[1] != portfolio.portfolio_id for case in cases])
        portfolio_holdouts[portfolio.portfolio_id] = _collapsed_rank_map(
            config_ids, element_costs, total_costs, mask, representatives, behavior_index
        )
    rng = np.random.default_rng(seed)
    bootstrap_ranks = np.empty((bootstrap_samples, len(representatives)), dtype=np.int32)
    for sample_index in range(bootstrap_samples):
        sampled = rng.integers(0, len(cases), size=len(cases))
        sample_order, sample_metrics = _rank_metrics(
            config_ids[representatives],
            element_costs[representatives][:, sampled],
            total_costs[representatives][:, sampled],
            np.ones(len(sampled), dtype=bool),
        )
        bootstrap_ranks[sample_index] = _competition_ranks(sample_order, sample_metrics)
    rows = []
    for index in order:
        index = int(index)
        config_id = int(config_ids[index])
        worst_column = int(np.argmax(element_costs[index]))
        worst_case_column = int(np.argmax(total_costs[index]))
        profile_means = {
            profile.profile_id: float(total_costs[index, [case[0] == profile.profile_id for case in cases]].mean())
            for profile in context.profiles
        }
        worst_profile_id = max(profile_means, key=profile_means.get)
        config = next(item for item in context.configs if item.config_id == config_id)
        sampled_ranks = bootstrap_ranks[:, behavior_index[index]]
        rows.append(
            {
                "rank": int(full_ranks[index]),
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
                "behavior_hash": behavior_hashes[index],
                "equivalent_behavior_count": len(behavior_groups[behavior_hashes[index]]),
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
    first = int(order[0])
    winner_key = _score_key(full_metrics, first)
    winner_indices = [int(index) for index in order if _score_key(full_metrics, int(index)) == winner_key]
    second = next(
        (int(index) for index in order if _score_key(full_metrics, int(index)) != winner_key),
        None,
    )
    if second is not None:
        winner_margin = {
            "worst_element_cost": float(element_costs[second].max() - element_costs[first].max()),
            "worst_case_cost": float(total_costs[second].max() - total_costs[first].max()),
            "mean_case_cost": float(total_costs[second].mean() - total_costs[first].mean()),
        }
    for row in rows:
        worst_profile_holdout = max(row["leave_one_profile_out_ranks"].values(), default=row["rank"])
        worst_portfolio_holdout = max(row["leave_one_portfolio_out_ranks"].values(), default=row["rank"])
        row["stability"] = {
            "worst_leave_one_profile_rank": worst_profile_holdout,
            "worst_leave_one_portfolio_rank": worst_portfolio_holdout,
            "worst_holdout_rank": max(worst_profile_holdout, worst_portfolio_holdout),
        }
    representative_rows = [row for row in rows if row["config_id"] == min(behavior_groups[row["behavior_hash"]])]
    stability_behavior_order = sorted(
        representative_rows,
        key=lambda row: (
            row["stability"]["worst_holdout_rank"],
            row["bootstrap"]["rank_p90"],
            row["rank"],
            row["config_id"],
        ),
    )
    previous_stability_key: tuple[float, ...] | None = None
    shared_stability_rank = 0
    stability_rank_by_behavior = {}
    for position, row in enumerate(stability_behavior_order, start=1):
        stability_key = (
            float(row["stability"]["worst_holdout_rank"]),
            round(float(row["bootstrap"]["rank_p90"]), 12),
            float(row["rank"]),
        )
        if stability_key != previous_stability_key:
            shared_stability_rank = position
            previous_stability_key = stability_key
        stability_rank_by_behavior[row["behavior_hash"]] = shared_stability_rank
    for row in rows:
        row["stability"]["rank"] = stability_rank_by_behavior[row["behavior_hash"]]
    stability_order = sorted(
        rows,
        key=lambda row: (row["stability"]["rank"], row["rank"], row["config_id"]),
    )
    leader = rows[0]
    leader_validation = {
        "config_id": leader["config_id"],
        "unique_full_ranking_leader": len({behavior_hashes[index] for index in winner_indices}) == 1,
        "worst_leave_one_profile_rank": leader["stability"]["worst_leave_one_profile_rank"],
        "worst_leave_one_portfolio_rank": leader["stability"]["worst_leave_one_portfolio_rank"],
        "bootstrap_rank_p90": leader["bootstrap"]["rank_p90"],
    }
    leader_validation["validated_winner"] = bool(
        leader_validation["unique_full_ranking_leader"]
        and leader_validation["worst_leave_one_profile_rank"] == 1
        and leader_validation["worst_leave_one_portfolio_rank"] == 1
        and leader_validation["bootstrap_rank_p90"] == 1.0
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "barrage_signature": context.signature,
        "source_matrix_signature": context.manifest["source_matrix_signature"],
        "selection": context.manifest["selection"],
        "case_count": len(cases),
        "config_count": len(config_ids),
        "behavior_count": len(representatives),
        "bootstrap_samples": bootstrap_samples,
        "analysis_model_sha256": hashlib.sha256(
            json.dumps(model, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
        "analysis_feature_structure": model.get("feature_structure", "independent"),
        "winner_config_ids": [int(config_ids[index]) for index in winner_indices],
        "winner_margin_to_second": winner_margin,
        "leader_validation": leader_validation,
        "stability_ranking_config_ids": [row["config_id"] for row in stability_order],
        "stability_ranking_behavior_representatives": [row["config_id"] for row in stability_behavior_order],
        "equivalent_behavior_groups": {
            digest: config_group for digest, config_group in behavior_groups.items() if len(config_group) > 1
        },
        "ranking": rows,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate learned solver preferences across the nutrient portfolio barrage."
    )
    parser.add_argument("--cases", type=Path, default=matrix.DEFAULT_CASES_PATH)
    parser.add_argument("--ranking", type=Path, default=preference.DEFAULT_RANKING_PATH)
    parser.add_argument("--model", type=Path, default=preference.DEFAULT_MODEL_PATH)
    parser.add_argument(
        "--analysis-model",
        type=Path,
        default=None,
        help="rescore stored solver outputs with this compatible preference model",
    )
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
    parser.add_argument(
        "--extend-shortlist",
        action="store_true",
        help="reuse a compatible database when the new shortlist is a strict superset",
    )
    parser.add_argument("--analysis-out", type=Path, default=None)
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
            if existing is None or (
                existing[0] != context.signature and not _stored_analysis_inputs_match(connection, context)
            ):
                raise ValueError("Barrage database does not match the requested analysis inputs")
        else:
            summary = run_barrage(args, context, connection)
            print(
                f"Barrage {summary['status']}: {summary['total_runs']:,}/"
                f"{summary['planned_solves']:,} solves in {summary['elapsed_seconds']:.2f}s"
            )
        if not args.skip_analysis:
            analysis_model_path = args.analysis_model or args.model
            model = json.loads(analysis_model_path.read_text(encoding="utf-8"))
            if str(model["matrix_signature"]) != context.manifest["source_matrix_signature"]:
                raise ValueError("Analysis model and stored solver matrix signatures differ")
            analysis = analyze_barrage(
                connection,
                context,
                model,
                bootstrap_samples=args.bootstrap_samples,
                seed=args.seed,
            )
            output = args.analysis_out or (args.out_dir / "barrage_ranking.json")
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(
                json.dumps(analysis, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            validation = analysis["leader_validation"]
            print(
                f"Barrage lexicographic leader: config {validation['config_id']} "
                f"({analysis['case_count']} profile-portfolio cases)"
            )
            if not validation["validated_winner"]:
                print(
                    "No validated winner: "
                    f"worst profile holdout rank={validation['worst_leave_one_profile_rank']}, "
                    f"worst portfolio holdout rank={validation['worst_leave_one_portfolio_rank']}, "
                    f"bootstrap p90 rank={validation['bootstrap_rank_p90']:.1f}"
                )
    finally:
        connection.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
