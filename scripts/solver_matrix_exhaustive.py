from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import os
import sqlite3
import struct
import sys
import time
import zlib
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
from horticalc.data_io import (  # noqa: E402
    Fertilizer,
    load_fertilizers,
    load_molar_masses,
    load_water_profile_data,
)
from horticalc.paths import logs_dir, resolve_water_profile_path  # noqa: E402

SCHEMA_VERSION = 1
DEFAULT_OUT_DIR = logs_dir(ROOT) / "solver_matrix" / "exhaustive"
CANONICAL_ELEMENT_ORDER = (
    "N_total",
    "N_NH4",
    "N_NO3",
    "N_UREA",
    "P",
    "K",
    "Ca",
    "Mg",
    "S",
    "Si",
    "Fe",
    "Mn",
    "Cu",
    "Zn",
    "B",
    "Mo",
    "Na",
    "Cl",
    "CO3",
    "HCO3",
)


@dataclass(frozen=True)
class ExhaustiveContext:
    cases: dict[str, Any]
    profiles: tuple[matrix.TargetProfile, ...]
    portfolio: matrix.FertilizerPortfolio
    fertilizers: dict[str, Fertilizer]
    molar_masses: dict[str, float]
    water_profile_name: str
    water_profile_data: dict[str, Any]
    osmosis_percent: float
    liters: float
    element_order: tuple[str, ...]
    config_count: int
    signature: str
    manifest: dict[str, Any]


@dataclass(frozen=True)
class CompactRun:
    profile_id: str
    status: str
    elapsed_seconds: float
    solution_hash: str | None
    achieved_vector: bytes | None
    objective_elements: tuple[str, ...]
    legacy_composite_score: float | None
    legacy_macro_score: float | None
    legacy_n_form_score: float | None
    legacy_micro_score: float | None
    legacy_other_score: float | None
    legacy_ignored_score: float | None
    total_grams: float | None
    used_fertilizer_count: int | None
    error: str


@dataclass(frozen=True)
class ConfigBatchResult:
    config_id: int
    runs: tuple[CompactRun, ...]


_WORKER_STATE: dict[str, Any] = {}


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(_json(value).encode("utf-8")).hexdigest()


def _hash_files(paths: Iterable[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths, key=lambda item: str(item)):
        digest.update(str(path.resolve()).encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _fertilizer_contract(fertilizers: dict[str, Fertilizer], names: Iterable[str]) -> dict[str, Any]:
    return {
        name: {
            "liquid": fertilizers[name].liquid,
            "weight_factor": fertilizers[name].weight_factor,
            "comp": fertilizers[name].comp,
            "solver_max_dose_per_l": fertilizers[name].solver_max_dose_per_l,
        }
        for name in names
    }


def _element_order(
    profiles: Iterable[matrix.TargetProfile],
    water_profile_data: dict[str, Any],
) -> tuple[str, ...]:
    keys = set(CANONICAL_ELEMENT_ORDER)
    keys.update(str(key) for key in (water_profile_data.get("mg_per_l") or {}))
    for profile in profiles:
        keys.update(profile.targets_mg_per_l)
    preferred = [key for key in CANONICAL_ELEMENT_ORDER if key in keys]
    preferred.extend(sorted(keys - set(preferred)))
    return tuple(preferred)


def _limited_config_count(cases: dict[str, Any], max_configs: int | None) -> int:
    total = matrix.exhaustive_solver_config_count(cases)
    return min(total, max_configs) if max_configs else total


def load_context(args: argparse.Namespace) -> ExhaustiveContext:
    cases = matrix._read_yaml(args.cases)
    if int(cases.get("schema_version") or 0) != 2:
        raise ValueError("solver matrix cases must use schema_version: 2")
    fertilizers = load_fertilizers()
    molar_masses = load_molar_masses()
    profiles = matrix.load_target_profiles(cases, args.profiles)
    portfolios = matrix.load_fertilizer_portfolios(cases, fertilizers)
    portfolio_id = str(args.primary_portfolio or cases["primary_portfolio"])
    if portfolio_id not in portfolios:
        raise ValueError(f"Unknown primary portfolio override: {portfolio_id}")
    portfolio = portfolios[portfolio_id]
    water_profile_name = args.water_profile or str(cases.get("water_profile") or "65936")
    osmosis_percent = float(args.osmosis_percent if args.osmosis_percent is not None else cases["osmosis_percent"])
    liters = float(args.liters if args.liters is not None else cases.get("liters") or 10.0)
    water_profile_data = dict(load_water_profile_data(resolve_water_profile_path(water_profile_name, ROOT)))
    water_profile_data["osmosis_percent"] = osmosis_percent
    element_order = _element_order(profiles, water_profile_data)
    config_count = _limited_config_count(cases, args.max_configs)

    source_hash = _hash_files(
        (
            args.cases,
            ROOT / "scripts" / "solver_matrix.py",
            ROOT / "src" / "horticalc" / "solver.py",
            ROOT / "src" / "horticalc" / "solver_config.py",
        )
    )
    contract = {
        "schema_version": SCHEMA_VERSION,
        "cases_sha256": hashlib.sha256(args.cases.read_bytes()).hexdigest(),
        "source_sha256": source_hash,
        "profiles": [asdict(profile) for profile in profiles],
        "portfolio": asdict(portfolio),
        "fertilizers": _fertilizer_contract(fertilizers, portfolio.fertilizers),
        "molar_masses": molar_masses,
        "water_profile_name": water_profile_name,
        "water_profile_data": water_profile_data,
        "osmosis_percent": osmosis_percent,
        "liters": liters,
        "element_order": element_order,
        "config_count": config_count,
        "parameter_values": matrix.exhaustive_parameter_values(cases),
    }
    signature = _sha256_json(contract)
    manifest = {
        **contract,
        "signature": signature,
        "runner_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "planned_runs": config_count * len(profiles),
        "storage": "normalized SQLite; achieved vectors deduplicated by exact SHA-256",
        "selection": "unweighted per-element Pareto dominance and data-normalized utopia distance",
    }
    return ExhaustiveContext(
        cases=cases,
        profiles=tuple(profiles),
        portfolio=portfolio,
        fertilizers=fertilizers,
        molar_masses=molar_masses,
        water_profile_name=water_profile_name,
        water_profile_data=water_profile_data,
        osmosis_percent=osmosis_percent,
        liters=liters,
        element_order=element_order,
        config_count=config_count,
        signature=signature,
        manifest=manifest,
    )


def _pack_vector(values: Iterable[float]) -> bytes:
    items = tuple(float(value) for value in values)
    return struct.pack(f"<{len(items)}d", *items)


def _unpack_vector(payload: bytes, size: int) -> np.ndarray:
    if len(payload) != size * 8:
        raise ValueError(f"Invalid vector byte count: expected {size * 8}, got {len(payload)}")
    return np.frombuffer(payload, dtype="<f8", count=size).copy()


def _mapping_vector(values: dict[str, Any], element_order: tuple[str, ...]) -> bytes:
    unknown = set(values) - set(element_order)
    if unknown:
        raise ValueError(f"Achieved solution contains unregistered elements: {', '.join(sorted(unknown))}")
    return _pack_vector(float(values.get(key, 0.0)) for key in element_order)


def _worker_initializer(payload: dict[str, Any]) -> None:
    _WORKER_STATE.clear()
    _WORKER_STATE.update(payload)


def _compact_row(row: dict[str, Any], element_order: tuple[str, ...]) -> CompactRun:
    if row["status"] != "ok":
        return CompactRun(
            profile_id=str(row["profile_id"]),
            status="error",
            elapsed_seconds=float(row.get("elapsed_seconds") or 0.0),
            solution_hash=None,
            achieved_vector=None,
            objective_elements=(),
            legacy_composite_score=None,
            legacy_macro_score=None,
            legacy_n_form_score=None,
            legacy_micro_score=None,
            legacy_other_score=None,
            legacy_ignored_score=None,
            total_grams=None,
            used_fertilizer_count=None,
            error=str(row.get("error") or "unknown solver failure"),
        )
    achieved = json.loads(row["achieved_elements_mg_per_l"])
    achieved_vector = _mapping_vector(achieved, element_order)
    return CompactRun(
        profile_id=str(row["profile_id"]),
        status="ok",
        elapsed_seconds=float(row["elapsed_seconds"]),
        solution_hash=hashlib.sha256(achieved_vector).hexdigest(),
        achieved_vector=achieved_vector,
        objective_elements=tuple(json.loads(row["objective_elements"])),
        legacy_composite_score=float(row["composite_score"]),
        legacy_macro_score=float(row["macro_score"]),
        legacy_n_form_score=float(row["n_form_score"]),
        legacy_micro_score=float(row["micro_score"]),
        legacy_other_score=float(row["other_score"]),
        legacy_ignored_score=float(row["ignored_score"]),
        total_grams=float(row["total_grams"]),
        used_fertilizer_count=int(row["used_fertilizer_count"]),
        error="",
    )


def _execute_config_task(task: tuple[int, str, dict[str, Any]]) -> ConfigBatchResult:
    config_id, config_hash, values = task
    state = _WORKER_STATE
    config = matrix.SolverConfigCase(
        experiment_id="exhaustive",
        config_id=config_hash,
        name=f"exhaustive:{config_hash[:16]}",
        values=values,
        varied_keys=(),
    )
    runs = []
    for profile in state["profiles"]:
        row = matrix.solve_case(
            profile=profile,
            portfolio=state["portfolio"],
            config=config,
            preset="exhaustive",
            phase="settings",
            liters=state["liters"],
            water_profile_name=state["water_profile_name"],
            osmosis_percent=state["osmosis_percent"],
            water_profile_data=state["water_profile_data"],
            fertilizers=state["fertilizers"],
            molar_masses=state["molar_masses"],
        )
        runs.append(_compact_row(row, state["element_order"]))
    return ConfigBatchResult(config_id=config_id, runs=tuple(runs))


def _worker_payload(context: ExhaustiveContext) -> dict[str, Any]:
    return {
        "profiles": context.profiles,
        "portfolio": context.portfolio,
        "fertilizers": context.fertilizers,
        "molar_masses": context.molar_masses,
        "water_profile_name": context.water_profile_name,
        "water_profile_data": context.water_profile_data,
        "osmosis_percent": context.osmosis_percent,
        "liters": context.liters,
        "element_order": context.element_order,
    }


def open_database(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA synchronous = NORMAL")
    connection.execute("PRAGMA temp_store = MEMORY")
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS profiles (
            profile_id TEXT PRIMARY KEY,
            ordinal INTEGER NOT NULL,
            name TEXT NOT NULL,
            group_name TEXT NOT NULL,
            source TEXT NOT NULL,
            targets_json TEXT NOT NULL,
            target_vector BLOB NOT NULL,
            objective_elements_json TEXT
        );
        CREATE TABLE IF NOT EXISTS portfolios (
            portfolio_id TEXT PRIMARY KEY,
            source TEXT NOT NULL,
            fertilizers_json TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS configs (
            config_id INTEGER PRIMARY KEY,
            config_hash TEXT NOT NULL UNIQUE,
            values_json TEXT NOT NULL,
            varied_keys_json TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS solutions (
            solution_id INTEGER PRIMARY KEY,
            solution_hash TEXT NOT NULL UNIQUE,
            achieved_vector BLOB NOT NULL
        );
        CREATE TABLE IF NOT EXISTS runs (
            config_id INTEGER NOT NULL REFERENCES configs(config_id),
            profile_id TEXT NOT NULL REFERENCES profiles(profile_id),
            portfolio_id TEXT NOT NULL REFERENCES portfolios(portfolio_id),
            solution_id INTEGER REFERENCES solutions(solution_id),
            status TEXT NOT NULL,
            elapsed_seconds REAL NOT NULL,
            legacy_composite_score REAL,
            legacy_macro_score REAL,
            legacy_n_form_score REAL,
            legacy_micro_score REAL,
            legacy_other_score REAL,
            legacy_ignored_score REAL,
            total_grams REAL,
            used_fertilizer_count INTEGER,
            error TEXT NOT NULL,
            PRIMARY KEY (config_id, profile_id, portfolio_id)
        );
        CREATE INDEX IF NOT EXISTS runs_profile_status_idx
            ON runs(profile_id, portfolio_id, status);
        CREATE INDEX IF NOT EXISTS runs_solution_idx ON runs(solution_id);
        CREATE TABLE IF NOT EXISTS pareto (
            profile_id TEXT NOT NULL,
            portfolio_id TEXT NOT NULL,
            solution_id INTEGER NOT NULL REFERENCES solutions(solution_id),
            representative_config_id INTEGER NOT NULL REFERENCES configs(config_id),
            utopia_distance REAL NOT NULL,
            is_knee INTEGER NOT NULL,
            PRIMARY KEY (profile_id, portfolio_id, solution_id)
        );
        CREATE TABLE IF NOT EXISTS finalists (
            profile_id TEXT NOT NULL,
            portfolio_id TEXT NOT NULL,
            config_id INTEGER NOT NULL REFERENCES configs(config_id),
            solution_id INTEGER NOT NULL REFERENCES solutions(solution_id),
            selection TEXT NOT NULL,
            rank INTEGER NOT NULL,
            full_result_zlib BLOB NOT NULL,
            PRIMARY KEY (profile_id, portfolio_id, config_id, selection)
        );
        """
    )
    return connection


def initialize_database(connection: sqlite3.Connection, context: ExhaustiveContext) -> bool:
    existing = connection.execute("SELECT value FROM meta WHERE key = 'signature'").fetchone()
    if existing is not None and existing[0] != context.signature:
        raise ValueError("Existing exhaustive database has a different input signature; use a new output directory")
    is_resume = existing is not None
    if is_resume:
        connection.execute("INSERT OR REPLACE INTO meta(key, value) VALUES ('status', 'running')")
    else:
        metadata = {
            "schema_version": str(SCHEMA_VERSION),
            "signature": context.signature,
            "manifest": _json(context.manifest),
            "status": "running",
        }
        connection.executemany(
            "INSERT INTO meta(key, value) VALUES (?, ?)",
            metadata.items(),
        )
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
                _mapping_vector(profile.targets_mg_per_l, context.element_order),
            ),
        )
    connection.execute(
        "INSERT OR IGNORE INTO portfolios(portfolio_id, source, fertilizers_json) VALUES (?, ?, ?)",
        (context.portfolio.portfolio_id, context.portfolio.source, _json(context.portfolio.fertilizers)),
    )
    connection.commit()
    return is_resume


def validate_database(connection: sqlite3.Connection, context: ExhaustiveContext) -> None:
    existing = connection.execute("SELECT value FROM meta WHERE key = 'signature'").fetchone()
    if existing is None:
        raise ValueError("The exhaustive database is not initialized; run the matrix before --analyze-only")
    if existing[0] != context.signature:
        raise ValueError("Existing exhaustive database has a different input signature; use matching inputs")


def _completed_config_ids(connection: sqlite3.Connection, context: ExhaustiveContext) -> set[int]:
    rows = connection.execute(
        """
        SELECT config_id
        FROM runs
        WHERE portfolio_id = ?
        GROUP BY config_id
        HAVING COUNT(DISTINCT profile_id) = ?
        """,
        (context.portfolio.portfolio_id, len(context.profiles)),
    )
    return {int(row[0]) for row in rows}


def _config_tasks(
    connection: sqlite3.Connection,
    context: ExhaustiveContext,
    completed: set[int],
) -> Iterator[tuple[int, str, dict[str, Any]]]:
    configs: Iterable[matrix.SolverConfigCase] = matrix.iter_exhaustive_solver_configs(context.cases)
    configs = itertools.islice(configs, context.config_count)
    for config_id, config in enumerate(configs, start=1):
        connection.execute(
            """
            INSERT OR IGNORE INTO configs(config_id, config_hash, values_json, varied_keys_json)
            VALUES (?, ?, ?, ?)
            """,
            (config_id, config.config_id, _json(config.values), _json(config.varied_keys)),
        )
        if config_id % 10_000 == 0:
            connection.commit()
        if config_id not in completed:
            yield config_id, config.config_id, config.values
    connection.commit()


class ResultWriter:
    def __init__(self, connection: sqlite3.Connection, context: ExhaustiveContext) -> None:
        self.connection = connection
        self.context = context
        self.solution_cache: OrderedDict[str, int] = OrderedDict()
        self.objectives = {
            str(profile_id): (tuple(json.loads(payload)) if payload else None)
            for profile_id, payload in connection.execute("SELECT profile_id, objective_elements_json FROM profiles")
        }

    def _solution_id(self, result: CompactRun) -> int | None:
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
        solution_id = (
            int(inserted[0])
            if inserted
            else int(
                self.connection.execute(
                    "SELECT solution_id FROM solutions WHERE solution_hash = ?",
                    (result.solution_hash,),
                ).fetchone()[0]
            )
        )
        self.solution_cache[result.solution_hash] = solution_id
        if len(self.solution_cache) > 100_000:
            self.solution_cache.popitem(last=False)
        return solution_id

    def _record_objectives(self, result: CompactRun) -> None:
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

    def write(self, batch: ConfigBatchResult) -> None:
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
                    self.context.portfolio.portfolio_id,
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


def _execute_serial(
    tasks: Iterable[tuple[int, str, dict[str, Any]]],
    writer: ResultWriter,
    payload: dict[str, Any],
    commit_every: int,
) -> int:
    _worker_initializer(payload)
    completed = 0
    for task in tasks:
        writer.write(_execute_config_task(task))
        completed += 1
        if completed % commit_every == 0:
            writer.connection.commit()
    return completed


def _execute_parallel(
    tasks: Iterable[tuple[int, str, dict[str, Any]]],
    writer: ResultWriter,
    payload: dict[str, Any],
    *,
    workers: int,
    queue_depth: int,
    commit_every: int,
) -> int:
    iterator = iter(tasks)
    pending: set[Future[ConfigBatchResult]] = set()
    completed = 0
    with ProcessPoolExecutor(
        max_workers=workers,
        initializer=_worker_initializer,
        initargs=(payload,),
    ) as executor:
        for _ in range(queue_depth):
            try:
                pending.add(executor.submit(_execute_config_task, next(iterator)))
            except StopIteration:
                break
        while pending:
            done, pending = wait(pending, return_when=FIRST_COMPLETED)
            for future in done:
                writer.write(future.result())
                completed += 1
                if completed % commit_every == 0:
                    writer.connection.commit()
                with suppress(StopIteration):
                    pending.add(executor.submit(_execute_config_task, next(iterator)))
    return completed


def run_exhaustive(
    args: argparse.Namespace, context: ExhaustiveContext, connection: sqlite3.Connection
) -> dict[str, Any]:
    is_resume = initialize_database(connection, context)
    completed_before = _completed_config_ids(connection, context)
    tasks = _config_tasks(connection, context, completed_before)
    writer = ResultWriter(connection, context)
    workers = args.workers or max(1, os.cpu_count() or 1)
    if workers < 1:
        raise ValueError("--workers must be >= 1")
    if args.queue_depth < 1:
        raise ValueError("--queue-depth must be >= 1")
    started = time.perf_counter()
    if workers == 1:
        executed = _execute_serial(tasks, writer, _worker_payload(context), args.commit_every)
    else:
        executed = _execute_parallel(
            tasks,
            writer,
            _worker_payload(context),
            workers=workers,
            queue_depth=args.queue_depth,
            commit_every=args.commit_every,
        )
    connection.commit()
    counts = dict(connection.execute("SELECT status, COUNT(*) FROM runs GROUP BY status").fetchall())
    total_runs = sum(int(value) for value in counts.values())
    planned_runs = context.config_count * len(context.profiles)
    status = "complete" if total_runs == planned_runs else "partial"
    connection.execute("INSERT OR REPLACE INTO meta(key, value) VALUES ('status', ?)", (status,))
    connection.commit()
    summary = {
        "schema_version": SCHEMA_VERSION,
        "signature": context.signature,
        "database": str(args.database),
        "resumed": is_resume,
        "workers": workers,
        "queue_depth": args.queue_depth,
        "config_count": context.config_count,
        "profile_count": len(context.profiles),
        "planned_runs": planned_runs,
        "total_runs": total_runs,
        "status_counts": counts,
        "executed_configs_this_invocation": executed,
        "elapsed_seconds": time.perf_counter() - started,
        "status": status,
    }
    (args.out_dir / "exhaustive_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def pareto_efficient_mask(costs: np.ndarray) -> np.ndarray:
    """Return an exact minimization Pareto mask without objective weights."""

    if costs.ndim != 2:
        raise ValueError("Pareto costs must be a two-dimensional array")
    if len(costs) == 0:
        return np.zeros(0, dtype=bool)
    if not np.isfinite(costs).all():
        raise ValueError("Pareto costs must contain only finite values")
    minima = costs.min(axis=0)
    ranges = costs.max(axis=0) - minima
    normalized = np.divide(costs - minima, ranges, out=np.zeros_like(costs), where=ranges > 0.0)
    order = np.argsort(np.square(normalized).mean(axis=1), kind="stable")
    ordered = costs[order]
    alive = np.ones(len(ordered), dtype=bool)
    for index in range(len(ordered)):
        if not alive[index]:
            continue
        candidates = np.flatnonzero(alive)
        candidate_costs = ordered[candidates]
        dominated = np.all(candidate_costs >= ordered[index], axis=1) & np.any(candidate_costs > ordered[index], axis=1)
        alive[candidates[dominated]] = False
    mask = np.zeros(len(costs), dtype=bool)
    mask[order[alive]] = True
    return mask


def _utopia_distances(pareto_costs: np.ndarray) -> np.ndarray:
    minima = pareto_costs.min(axis=0)
    ranges = pareto_costs.max(axis=0) - minima
    normalized = np.divide(
        pareto_costs - minima,
        ranges,
        out=np.zeros_like(pareto_costs),
        where=ranges > 0.0,
    )
    return np.sqrt(np.square(normalized).mean(axis=1))


def _profile_candidates(
    connection: sqlite3.Connection,
    profile_id: str,
    portfolio_id: str,
) -> list[sqlite3.Row]:
    connection.row_factory = sqlite3.Row
    rows = connection.execute(
        """
        WITH representatives AS (
            SELECT solution_id, MIN(config_id) AS representative_config_id
            FROM runs
            WHERE profile_id = ? AND portfolio_id = ? AND status = 'ok'
            GROUP BY solution_id
        )
        SELECT
            representatives.solution_id,
            representatives.representative_config_id,
            s.solution_hash,
            s.achieved_vector,
            c.config_hash,
            c.values_json
        FROM representatives
        JOIN solutions AS s ON s.solution_id = representatives.solution_id
        JOIN configs AS c ON c.config_id = representatives.representative_config_id
        ORDER BY c.config_hash, s.solution_hash
        """,
        (profile_id, portfolio_id),
    ).fetchall()
    connection.row_factory = None
    return rows


def _rerun_finalist(
    connection: sqlite3.Connection,
    context: ExhaustiveContext,
    profile: matrix.TargetProfile,
    config_id: int,
    expected_solution_id: int,
    selection: str,
    rank: int,
) -> None:
    config_hash, values_json = connection.execute(
        "SELECT config_hash, values_json FROM configs WHERE config_id = ?",
        (config_id,),
    ).fetchone()
    config = matrix.SolverConfigCase(
        experiment_id="exhaustive",
        config_id=str(config_hash),
        name=f"exhaustive:{str(config_hash)[:16]}",
        values=json.loads(values_json),
        varied_keys=(),
    )
    row = matrix.solve_case(
        profile=profile,
        portfolio=context.portfolio,
        config=config,
        preset="exhaustive",
        phase="finalist",
        liters=context.liters,
        water_profile_name=context.water_profile_name,
        osmosis_percent=context.osmosis_percent,
        water_profile_data=context.water_profile_data,
        fertilizers=context.fertilizers,
        molar_masses=context.molar_masses,
    )
    compact = _compact_row(row, context.element_order)
    expected_hash = connection.execute(
        "SELECT solution_hash FROM solutions WHERE solution_id = ?",
        (expected_solution_id,),
    ).fetchone()[0]
    if compact.solution_hash != expected_hash:
        raise ValueError(f"Finalist rerun was not deterministic for profile {profile.profile_id}")
    payload = zlib.compress(_json(row).encode("utf-8"), level=9)
    connection.execute(
        """
        INSERT OR REPLACE INTO finalists(
            profile_id, portfolio_id, config_id, solution_id, selection, rank, full_result_zlib
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            profile.profile_id,
            context.portfolio.portfolio_id,
            config_id,
            expected_solution_id,
            selection,
            rank,
            payload,
        ),
    )


def _config_details(connection: sqlite3.Connection, config_id: int) -> dict[str, Any]:
    config_hash, values_json = connection.execute(
        "SELECT config_hash, values_json FROM configs WHERE config_id = ?",
        (config_id,),
    ).fetchone()
    return {
        "config_id": config_id,
        "config_hash": str(config_hash),
        "solver_config": json.loads(values_json),
    }


def _global_configuration_analysis(
    context: ExhaustiveContext,
    connection: sqlite3.Connection,
    element_index: dict[str, int],
) -> dict[str, Any] | None:
    complete_config_ids = [
        int(row[0])
        for row in connection.execute(
            """
            SELECT config_id
            FROM runs
            WHERE portfolio_id = ? AND status = 'ok'
            GROUP BY config_id
            HAVING COUNT(*) = ?
            ORDER BY config_id
            """,
            (context.portfolio.portfolio_id, len(context.profiles)),
        )
    ]
    if not complete_config_ids:
        return None

    objective_elements: dict[str, tuple[str, ...]] = {}
    profile_slices: dict[str, slice] = {}
    coordinate_count = 0
    for profile in context.profiles:
        payload = connection.execute(
            "SELECT objective_elements_json FROM profiles WHERE profile_id = ?",
            (profile.profile_id,),
        ).fetchone()
        if payload is None or not payload[0]:
            return None
        elements = tuple(json.loads(payload[0]))
        objective_elements[profile.profile_id] = elements
        profile_slices[profile.profile_id] = slice(coordinate_count, coordinate_count + len(elements))
        coordinate_count += len(elements)

    row_by_config = {config_id: index for index, config_id in enumerate(complete_config_ids)}
    config_hash_by_id = {
        int(config_id): str(config_hash)
        for config_id, config_hash in connection.execute("SELECT config_id, config_hash FROM configs")
    }
    costs = np.full((len(complete_config_ids), coordinate_count), np.nan, dtype=float)
    for profile in context.profiles:
        elements = objective_elements[profile.profile_id]
        indices = [element_index[key] for key in elements]
        target = np.array([float(profile.targets_mg_per_l.get(key, 0.0)) for key in elements])
        profile_slice = profile_slices[profile.profile_id]
        for config_id, achieved_payload in connection.execute(
            """
            SELECT r.config_id, s.achieved_vector
            FROM runs AS r
            JOIN solutions AS s ON s.solution_id = r.solution_id
            WHERE r.profile_id = ? AND r.portfolio_id = ? AND r.status = 'ok'
            """,
            (profile.profile_id, context.portfolio.portfolio_id),
        ):
            row_index = row_by_config.get(int(config_id))
            if row_index is None:
                continue
            achieved = _unpack_vector(achieved_payload, len(context.element_order))[indices]
            costs[row_index, profile_slice] = np.abs(achieved - target)
    if not np.isfinite(costs).all():
        raise ValueError("Complete configurations produced an incomplete global objective matrix")

    minima = costs.min(axis=0)
    ranges = costs.max(axis=0) - minima
    normalized = np.divide(costs - minima, ranges, out=np.zeros_like(costs), where=ranges > 0.0)
    distances = np.sqrt(np.square(normalized).mean(axis=1))
    minimum_distance = float(distances.min())
    tied_positions = np.flatnonzero(distances == minimum_distance)
    winner_position = min(
        (int(position) for position in tied_positions),
        key=lambda position: config_hash_by_id[complete_config_ids[position]],
    )
    winner_config_id = complete_config_ids[winner_position]
    winner = {
        **_config_details(connection, winner_config_id),
        "utopia_distance": minimum_distance,
        "profile_normalized_rms": {
            profile.profile_id: float(
                np.sqrt(np.square(normalized[winner_position, profile_slices[profile.profile_id]]).mean())
            )
            for profile in context.profiles
        },
        "signed_errors_mg_per_l": {},
    }
    for profile in context.profiles:
        solution_id, achieved_payload = connection.execute(
            """
            SELECT r.solution_id, s.achieved_vector
            FROM runs AS r
            JOIN solutions AS s ON s.solution_id = r.solution_id
            WHERE r.config_id = ? AND r.profile_id = ? AND r.portfolio_id = ?
            """,
            (winner_config_id, profile.profile_id, context.portfolio.portfolio_id),
        ).fetchone()
        elements = objective_elements[profile.profile_id]
        achieved = _unpack_vector(achieved_payload, len(context.element_order))
        winner["signed_errors_mg_per_l"][profile.profile_id] = {
            key: float(achieved[element_index[key]] - profile.targets_mg_per_l.get(key, 0.0)) for key in elements
        }
        _rerun_finalist(
            connection,
            context,
            profile,
            winner_config_id,
            int(solution_id),
            "global_utopia",
            1,
        )

    legacy_row = connection.execute(
        """
        SELECT r.config_id, AVG(r.legacy_composite_score) AS average_score
        FROM runs AS r
        JOIN configs AS c ON c.config_id = r.config_id
        WHERE r.portfolio_id = ? AND r.status = 'ok'
        GROUP BY r.config_id, c.config_hash
        HAVING COUNT(*) = ?
        ORDER BY average_score, c.config_hash
        LIMIT 1
        """,
        (context.portfolio.portfolio_id, len(context.profiles)),
    ).fetchone()
    legacy = None
    if legacy_row is not None:
        legacy_config_id = int(legacy_row[0])
        legacy = {
            **_config_details(connection, legacy_config_id),
            "average_score": float(legacy_row[1]),
        }
        for profile in context.profiles:
            solution_id = connection.execute(
                """
                SELECT solution_id FROM runs
                WHERE config_id = ? AND profile_id = ? AND portfolio_id = ?
                """,
                (legacy_config_id, profile.profile_id, context.portfolio.portfolio_id),
            ).fetchone()[0]
            _rerun_finalist(
                connection,
                context,
                profile,
                legacy_config_id,
                int(solution_id),
                "legacy_global_composite",
                1,
            )

    connection.commit()
    return {
        "complete_config_count": len(complete_config_ids),
        "objective_coordinate_count": coordinate_count,
        "utopia": winner,
        "legacy_composite_best": legacy,
    }


def analyze_database(
    args: argparse.Namespace,
    context: ExhaustiveContext,
    connection: sqlite3.Connection,
) -> dict[str, Any]:
    summaries = []
    element_index = {key: index for index, key in enumerate(context.element_order)}
    for profile in context.profiles:
        objective_payload = connection.execute(
            "SELECT objective_elements_json FROM profiles WHERE profile_id = ?",
            (profile.profile_id,),
        ).fetchone()
        if objective_payload is None or not objective_payload[0]:
            continue
        objective_elements = tuple(json.loads(objective_payload[0]))
        objective_indices = [element_index[key] for key in objective_elements]
        target_vector = np.array(
            [float(profile.targets_mg_per_l.get(key, 0.0)) for key in context.element_order],
            dtype=float,
        )
        candidates = _profile_candidates(connection, profile.profile_id, context.portfolio.portfolio_id)
        if not candidates:
            continue
        achieved = np.vstack([_unpack_vector(row["achieved_vector"], len(context.element_order)) for row in candidates])
        signed_errors = achieved[:, objective_indices] - target_vector[objective_indices]
        costs = np.abs(signed_errors)
        pareto_mask = pareto_efficient_mask(costs)
        pareto_positions = np.flatnonzero(pareto_mask)
        pareto_costs = costs[pareto_positions]
        distances = _utopia_distances(pareto_costs)
        tie_order = sorted(
            range(len(pareto_positions)),
            key=lambda index: (
                float(distances[index]),
                str(candidates[int(pareto_positions[index])]["config_hash"]),
                str(candidates[int(pareto_positions[index])]["solution_hash"]),
            ),
        )
        knee_local_index = tie_order[0]
        knee_position = int(pareto_positions[knee_local_index])
        connection.execute(
            "DELETE FROM pareto WHERE profile_id = ? AND portfolio_id = ?",
            (profile.profile_id, context.portfolio.portfolio_id),
        )
        for local_index, position in enumerate(pareto_positions):
            row = candidates[int(position)]
            connection.execute(
                """
                INSERT INTO pareto(
                    profile_id, portfolio_id, solution_id, representative_config_id,
                    utopia_distance, is_knee
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    profile.profile_id,
                    context.portfolio.portfolio_id,
                    int(row["solution_id"]),
                    int(row["representative_config_id"]),
                    float(distances[local_index]),
                    int(int(position) == knee_position),
                ),
            )
        knee = candidates[knee_position]
        legacy = connection.execute(
            """
            SELECT r.config_id, r.solution_id, r.legacy_composite_score, c.config_hash
            FROM runs AS r
            JOIN configs AS c ON c.config_id = r.config_id
            WHERE r.profile_id = ? AND r.portfolio_id = ? AND r.status = 'ok'
            ORDER BY r.legacy_composite_score, c.config_hash
            LIMIT 1
            """,
            (profile.profile_id, context.portfolio.portfolio_id),
        ).fetchone()
        connection.execute(
            "DELETE FROM finalists WHERE profile_id = ? AND portfolio_id = ?",
            (profile.profile_id, context.portfolio.portfolio_id),
        )
        finalist_positions = tie_order[: args.finalists_per_profile]
        for rank, local_index in enumerate(finalist_positions, start=1):
            candidate = candidates[int(pareto_positions[local_index])]
            _rerun_finalist(
                connection,
                context,
                profile,
                int(candidate["representative_config_id"]),
                int(candidate["solution_id"]),
                "pareto_utopia",
                rank,
            )
        if legacy is not None:
            _rerun_finalist(
                connection,
                context,
                profile,
                int(legacy[0]),
                int(legacy[1]),
                "legacy_composite",
                1,
            )
        knee_error = signed_errors[knee_position]
        summaries.append(
            {
                "profile_id": profile.profile_id,
                "candidate_solution_count": len(candidates),
                "pareto_solution_count": len(pareto_positions),
                "knee": {
                    "solution_hash": knee["solution_hash"],
                    "config_hash": knee["config_hash"],
                    "config_id": int(knee["representative_config_id"]),
                    "solver_config": json.loads(knee["values_json"]),
                    "utopia_distance": float(distances[knee_local_index]),
                    "signed_errors_mg_per_l": {
                        key: float(value) for key, value in zip(objective_elements, knee_error, strict=True)
                    },
                },
                "legacy_composite_best": (
                    {
                        "config_hash": legacy[3],
                        "config_id": int(legacy[0]),
                        "solver_config": _config_details(connection, int(legacy[0]))["solver_config"],
                        "solution_id": int(legacy[1]),
                        "score": float(legacy[2]),
                    }
                    if legacy is not None
                    else None
                ),
            }
        )
        connection.commit()
    global_selection = _global_configuration_analysis(context, connection, element_index)
    analysis = {
        "schema_version": SCHEMA_VERSION,
        "signature": context.signature,
        "selection": {
            "dominance": "absolute per-objective error in mg/L; no element weights",
            "knee": "minimum RMS distance to the Pareto ideal after per-objective Pareto min/max normalization",
            "global": "minimum RMS distance after independent min/max normalization of every profile-element coordinate",
            "legacy_composite_retained_for_comparison": True,
        },
        "profiles": summaries,
        "global_selection": global_selection,
    }
    (args.out_dir / "pareto_analysis.json").write_text(
        json.dumps(analysis, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return analysis


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the deduplicated, parallel exhaustive Horticalc solver matrix.")
    parser.add_argument("--cases", type=Path, default=matrix.DEFAULT_CASES_PATH)
    parser.add_argument("--profiles", default="all")
    parser.add_argument("--primary-portfolio", default=None)
    parser.add_argument("--water-profile", default=None)
    parser.add_argument("--osmosis-percent", type=float, default=None)
    parser.add_argument("--liters", type=float, default=None)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--workers", type=int, default=0, help="0 uses the logical CPU count")
    parser.add_argument("--queue-depth", type=int, default=10_000)
    parser.add_argument("--commit-every", type=int, default=1_000)
    parser.add_argument("--max-configs", type=int, default=None)
    parser.add_argument("--finalists-per-profile", type=int, default=25)
    parser.add_argument("--analyze-only", action="store_true")
    parser.add_argument("--skip-analysis", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.max_configs is not None and args.max_configs < 1:
        raise ValueError("--max-configs must be >= 1")
    if args.commit_every < 1:
        raise ValueError("--commit-every must be >= 1")
    if args.finalists_per_profile < 1:
        raise ValueError("--finalists-per-profile must be >= 1")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    args.database = args.out_dir / "exhaustive.sqlite3"
    context = load_context(args)
    connection = open_database(args.database)
    try:
        if args.analyze_only:
            validate_database(connection, context)
            analysis = analyze_database(args, context, connection)
            print(f"Pareto analysis complete: {len(analysis['profiles'])} profiles")
            return 0
        summary = run_exhaustive(args, context, connection)
        print(
            f"Exhaustive matrix {summary['status']}: {summary['total_runs']}/"
            f"{summary['planned_runs']} runs, {summary['workers']} workers"
        )
        print(f"SQLite database: {args.database}")
        if not args.skip_analysis:
            analysis = analyze_database(args, context, connection)
            print(f"Pareto analysis complete: {len(analysis['profiles'])} profiles")
        return 0
    finally:
        connection.close()


if __name__ == "__main__":
    raise SystemExit(main())
