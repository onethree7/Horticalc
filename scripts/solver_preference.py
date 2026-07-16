from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import sqlite3
import sys
from pathlib import Path
from typing import Any, Iterable

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from horticalc.paths import logs_dir  # noqa: E402

SCHEMA_VERSION = 1
DEFAULT_RUN_DIR = logs_dir(ROOT) / "solver_matrix" / "exhaustive_001"
DEFAULT_DATABASE = DEFAULT_RUN_DIR / "exhaustive.sqlite3"
DEFAULT_PAIR_PATH = DEFAULT_RUN_DIR / "preference_pairs.jsonl"
DEFAULT_LABEL_PATH = DEFAULT_RUN_DIR / "preference_labels.jsonl"
DEFAULT_MODEL_PATH = DEFAULT_RUN_DIR / "preference_model.json"
DEFAULT_RANKING_PATH = DEFAULT_RUN_DIR / "preference_ranking.json"
REFERENCE_CONFIG_IDS = (69_630, 207_711)
DISPLAY_ELEMENT_ORDER = (
    "N_total",
    "N_NH4",
    "N_NO3",
    "N_UREA",
    "P",
    "K",
    "Ca",
    "Mg",
    "S",
    "Fe",
    "Mn",
    "Cu",
    "Zn",
    "B",
    "Mo",
    "Si",
    "Cl",
    "Na",
    "CO3",
    "HCO3",
)
DISPLAY_ELEMENT_NAMES = {
    "N_total": "N gesamt",
    "N_NH4": "Ammonium-N",
    "N_NO3": "Nitrat-N",
    "N_UREA": "Harnstoff-N",
    "B": "Bor",
}


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_number}: expected a JSON object")
        rows.append(value)
    return rows


def _write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text("".join(f"{_json(row)}\n" for row in rows), encoding="utf-8")
    temporary.replace(path)


def _unpack_vector(payload: bytes, size: int) -> np.ndarray:
    if len(payload) != size * 8:
        raise ValueError(f"Invalid achieved vector size: expected {size * 8}, got {len(payload)}")
    return np.frombuffer(payload, dtype="<f8", count=size).copy()


class MatrixDatabase:
    def __init__(self, path: Path) -> None:
        self.path = path
        if not path.exists():
            raise ValueError(f"Exhaustive matrix database does not exist: {path}")
        self.connection = sqlite3.connect(f"file:{path.resolve().as_posix()}?mode=ro", uri=True)
        manifest_row = self.connection.execute("SELECT value FROM meta WHERE key = 'manifest'").fetchone()
        if manifest_row is None:
            raise ValueError("Exhaustive matrix database has no manifest")
        self.manifest = json.loads(manifest_row[0])
        self.signature = str(self.manifest["signature"])
        self.element_order = tuple(str(value) for value in self.manifest["element_order"])
        self.element_index = {key: index for index, key in enumerate(self.element_order)}
        self.profiles = {str(profile["profile_id"]): profile for profile in self.manifest.get("profiles") or []}
        self.profile_order = tuple(self.profiles)
        self.portfolio_id = str(self.manifest["portfolio"]["portfolio_id"])
        self._reachable_spans: dict[str, dict[str, float]] = {}

    def close(self) -> None:
        self.connection.close()

    def config(self, config_id: int) -> dict[str, Any]:
        row = self.connection.execute(
            "SELECT config_hash, values_json FROM configs WHERE config_id = ?", (config_id,)
        ).fetchone()
        if row is None:
            raise ValueError(f"Unknown configuration id: {config_id}")
        return {"config_id": config_id, "config_hash": row[0], "solver_config": json.loads(row[1])}

    def objective_elements(self, profile_id: str) -> tuple[str, ...]:
        row = self.connection.execute(
            "SELECT objective_elements_json FROM profiles WHERE profile_id = ?", (profile_id,)
        ).fetchone()
        if row is None or not row[0]:
            raise ValueError(f"Profile has no objective element contract: {profile_id}")
        return tuple(json.loads(row[0]))

    def solution(self, profile_id: str, solution_id: int, config_id: int) -> dict[str, Any]:
        row = self.connection.execute(
            "SELECT solution_hash, achieved_vector FROM solutions WHERE solution_id = ?", (solution_id,)
        ).fetchone()
        if row is None:
            raise ValueError(f"Unknown solution id: {solution_id}")
        achieved_vector = _unpack_vector(row[1], len(self.element_order))
        targets = self.profiles[profile_id]["targets_mg_per_l"]
        elements = self.objective_elements(profile_id)
        target_values = {key: float(targets.get(key, 0.0)) for key in elements}
        achieved_values = {key: float(achieved_vector[self.element_index[key]]) for key in elements}
        errors = {key: achieved_values[key] - target_values[key] for key in elements}
        return {
            "solution_id": solution_id,
            "solution_hash": str(row[0]),
            **self.config(config_id),
            "targets_mg_per_l": target_values,
            "achieved_mg_per_l": achieved_values,
            "signed_errors_mg_per_l": errors,
            "reachable_error_span_mg_per_l": self.reachable_spans(profile_id),
        }

    def reachable_spans(self, profile_id: str) -> dict[str, float]:
        cached = self._reachable_spans.get(profile_id)
        if cached is not None:
            return cached
        elements = self.objective_elements(profile_id)
        indices = tuple(self.element_index[key] for key in elements)
        low = np.full(len(elements), np.inf, dtype=float)
        high = np.full(len(elements), -np.inf, dtype=float)
        rows = self.connection.execute(
            """
            SELECT s.achieved_vector
            FROM pareto AS p
            JOIN solutions AS s ON s.solution_id = p.solution_id
            WHERE p.profile_id = ? AND p.portfolio_id = ?
            """,
            (profile_id, self.portfolio_id),
        )
        for (payload,) in rows:
            vector = _unpack_vector(payload, len(self.element_order))
            values = vector[list(indices)]
            low = np.minimum(low, values)
            high = np.maximum(high, values)
        spans = {element: max(float(high[index] - low[index]), 1e-12) for index, element in enumerate(elements)}
        self._reachable_spans[profile_id] = spans
        return spans

    def pareto_solutions(self, profile_id: str) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            """
            SELECT p.solution_id, p.representative_config_id, p.is_knee, p.utopia_distance
            FROM pareto AS p
            WHERE p.profile_id = ? AND p.portfolio_id = ?
            ORDER BY p.is_knee DESC, p.utopia_distance, p.solution_id
            """,
            (profile_id, self.portfolio_id),
        ).fetchall()
        return [
            {
                **self.solution(profile_id, int(solution_id), int(config_id)),
                "is_knee": bool(is_knee),
                "utopia_distance": float(distance),
            }
            for solution_id, config_id, is_knee, distance in rows
        ]

    def config_solution(self, profile_id: str, config_id: int) -> dict[str, Any] | None:
        row = self.connection.execute(
            """
            SELECT solution_id FROM runs
            WHERE config_id = ? AND profile_id = ? AND portfolio_id = ? AND status = 'ok'
            """,
            (config_id, profile_id, self.portfolio_id),
        ).fetchone()
        return self.solution(profile_id, int(row[0]), config_id) if row else None


def raw_features(solution: dict[str, Any], element_order: tuple[str, ...]) -> dict[str, float]:
    targets = solution["targets_mg_per_l"]
    errors = solution["signed_errors_mg_per_l"]
    reachable_spans = solution.get("reachable_error_span_mg_per_l") or {}
    features: dict[str, float] = {}
    for element in element_order:
        if element not in errors:
            continue
        error = float(errors[element])
        target = float(targets.get(element, 0.0))
        under = max(-error, 0.0)
        over = max(error, 0.0)
        features[f"{element}:under_mg"] = under
        features[f"{element}:over_mg"] = over
        if target > 0.0:
            features[f"{element}:under_relative"] = under / target
            features[f"{element}:over_relative"] = over / target
        reachable_span = float(reachable_spans.get(element, 0.0))
        if reachable_span > 0.0:
            features[f"{element}:under_reachable"] = under / reachable_span
            features[f"{element}:over_reachable"] = over / reachable_span
    return features


def _solution_metrics(solution: dict[str, Any]) -> tuple[float, float]:
    errors = solution["signed_errors_mg_per_l"]
    macro_keys = tuple(key for key in ("N_total", "P", "K", "Ca", "Mg", "S", "Si") if key in errors)
    micro_keys = tuple(key for key in ("Fe", "Mn", "Cu", "Zn", "B", "Mo") if key in errors)
    macro = math.sqrt(sum(float(errors[key]) ** 2 for key in macro_keys) / max(1, len(macro_keys)))
    micro = math.sqrt(sum(float(errors[key]) ** 2 for key in micro_keys) / max(1, len(micro_keys)))
    return macro, micro


def _candidate_subset(
    database: MatrixDatabase,
    profile_id: str,
    *,
    maximum: int,
) -> list[dict[str, Any]]:
    candidates = database.pareto_solutions(profile_id)
    selected: dict[int, dict[str, Any]] = {}

    def add(solution: dict[str, Any] | None) -> None:
        if solution is not None:
            selected[int(solution["solution_id"])] = solution

    for solution in candidates:
        if solution.get("is_knee"):
            add(solution)
    for config_id in REFERENCE_CONFIG_IDS:
        add(database.config_solution(profile_id, config_id))
    elements = database.objective_elements(profile_id)
    for element in elements:
        add(min(candidates, key=lambda value: abs(value["signed_errors_mg_per_l"][element])))
        add(max(candidates, key=lambda value: abs(value["signed_errors_mg_per_l"][element])))
    add(min(candidates, key=lambda value: _solution_metrics(value)[0]))
    add(min(candidates, key=lambda value: _solution_metrics(value)[1]))

    remaining = [value for value in candidates if int(value["solution_id"]) not in selected]
    remaining.sort(key=lambda value: str(value["solution_hash"]))
    room = max(0, maximum - len(selected))
    if room and remaining:
        positions = np.linspace(0, len(remaining) - 1, min(room, len(remaining)), dtype=int)
        for position in positions:
            add(remaining[int(position)])
    return list(selected.values())


def _normalized_costs(
    candidates: list[dict[str, Any]],
    elements: tuple[str, ...],
) -> np.ndarray:
    costs = np.array(
        [[abs(float(candidate["signed_errors_mg_per_l"][element])) for element in elements] for candidate in candidates]
    )
    low = costs.min(axis=0)
    ranges = costs.max(axis=0) - low
    return np.divide(costs - low, ranges, out=np.zeros_like(costs), where=ranges > 0.0)


def _pair_priority(cost_a: np.ndarray, cost_b: np.ndarray) -> float:
    differences = cost_a - cost_b
    better_a = int(np.count_nonzero(differences < -1e-12))
    better_b = int(np.count_nonzero(differences > 1e-12))
    if not better_a or not better_b:
        return -1.0
    conflict_balance = min(better_a, better_b) / max(better_a, better_b)
    distance = float(np.sqrt(np.square(differences).mean()))
    return distance * (0.5 + 0.5 * conflict_balance)


def _pair_record(
    database: MatrixDatabase,
    profile_id: str,
    a: dict[str, Any],
    b: dict[str, Any],
    priority: float,
    *,
    selection: str = "objective_conflict",
    predicted_probability_a: float | None = None,
) -> dict[str, Any]:
    if str(b["solution_hash"]) < str(a["solution_hash"]):
        a, b = b, a
        if predicted_probability_a is not None:
            predicted_probability_a = 1.0 - predicted_probability_a
    pair_id = hashlib.sha256(
        f"{database.signature}:{profile_id}:{a['solution_hash']}:{b['solution_hash']}".encode()
    ).hexdigest()
    record = {
        "schema_version": SCHEMA_VERSION,
        "pair_id": pair_id,
        "matrix_signature": database.signature,
        "profile_id": profile_id,
        "priority": priority,
        "selection": selection,
        "a": a,
        "b": b,
    }
    if predicted_probability_a is not None:
        record["predicted_preference_probability_a"] = predicted_probability_a
    return record


def generate_pairs(
    database: MatrixDatabase,
    *,
    count: int,
    candidate_limit: int,
    seed: int,
    model: dict[str, Any] | None = None,
    excluded_pair_ids: set[str] | None = None,
) -> list[dict[str, Any]]:
    if model is not None and str(model["matrix_signature"]) != database.signature:
        raise ValueError("Preference model and exhaustive database signatures differ")
    excluded_pair_ids = excluded_pair_ids or set()
    rng = np.random.default_rng(seed)
    per_profile: dict[str, list[dict[str, Any]]] = {}
    for profile_id in database.profile_order:
        candidates = _candidate_subset(database, profile_id, maximum=candidate_limit)
        elements = database.objective_elements(profile_id)
        normalized = _normalized_costs(candidates, elements)
        learned_costs = (
            np.array([solution_cost(candidate, model) for candidate in candidates]) if model is not None else None
        )
        possible_pairs = len(candidates) * (len(candidates) - 1) // 2
        sample_count = min(max(count * 40, 10_000), possible_pairs)
        ranked: list[tuple[float, float, int, int]] = []
        all_pairs = list(itertools.combinations(range(len(candidates)), 2))
        if sample_count < len(all_pairs):
            selected_indices = rng.choice(len(all_pairs), size=sample_count, replace=False)
            sampled_pairs = (all_pairs[int(index)] for index in selected_indices)
        else:
            sampled_pairs = iter(all_pairs)
        for left, right in sampled_pairs:
            priority = _pair_priority(normalized[left], normalized[right])
            if priority >= 0.0:
                uncertainty = 0.0
                if learned_costs is not None:
                    uncertainty = abs(learned_costs[right] - learned_costs[left])
                ranked.append((uncertainty, priority, left, right))
        ranked.sort(
            key=lambda value: (
                value[0] if model is not None else 0.0,
                -value[1],
                str(candidates[value[2]]["solution_hash"]),
                str(candidates[value[3]]["solution_hash"]),
            )
        )
        records = []
        for _uncertainty, priority, left, right in ranked:
            record = _pair_record(
                database,
                profile_id,
                candidates[left],
                candidates[right],
                priority,
                selection="model_uncertainty" if model is not None else "objective_conflict",
                predicted_probability_a=(
                    float(_sigmoid(np.array([learned_costs[right] - learned_costs[left]]))[0])
                    if learned_costs is not None
                    else None
                ),
            )
            if record["pair_id"] not in excluded_pair_ids:
                records.append(record)
        per_profile[profile_id] = records

    pairs: list[dict[str, Any]] = []
    position = 0
    while len(pairs) < count:
        added = False
        for profile_id in database.profile_order:
            profile_pairs = per_profile[profile_id]
            if position < len(profile_pairs):
                pairs.append(profile_pairs[position])
                added = True
                if len(pairs) == count:
                    break
        if not added:
            break
        position += 1
    return pairs


def load_labels(path: Path) -> dict[str, dict[str, Any]]:
    labels = {}
    for row in _read_jsonl(path):
        choice = str(row.get("choice") or "").upper()
        if choice not in {"A", "B", "SKIP"}:
            raise ValueError(f"Invalid preference choice for {row.get('pair_id')}: {choice}")
        labels[str(row["pair_id"])] = {**row, "choice": choice}
    return labels


def save_label(path: Path, pair: dict[str, Any], choice: str) -> None:
    normalized = choice.upper()
    if normalized not in {"A", "B", "SKIP"}:
        raise ValueError("Choice must be A, B, or SKIP")
    labels = load_labels(path)
    labels[pair["pair_id"]] = {
        "schema_version": SCHEMA_VERSION,
        "pair_id": pair["pair_id"],
        "matrix_signature": pair["matrix_signature"],
        "profile_id": pair["profile_id"],
        "choice": normalized,
    }
    _write_jsonl(path, (labels[key] for key in sorted(labels)))


def _display_decimals(target: float) -> int:
    magnitude = abs(target)
    if magnitude >= 1.0:
        return 3
    if magnitude >= 0.1:
        return 4
    return 5


def _format_decimal(value: float, decimals: int, *, signed: bool = False) -> str:
    threshold = 0.5 * 10 ** (-decimals)
    normalized = 0.0 if abs(value) < threshold else value
    sign = "+" if signed else ""
    return f"{normalized:{sign}.{decimals}f}"


def _format_percent(error: float, target: float) -> str:
    if target == 0.0:
        return "-"
    percentage = error / target * 100.0
    if abs(percentage) < 0.005:
        percentage = 0.0
    return f"{percentage:+.2f} %"


def _ordered_pair_elements(pair: dict[str, Any]) -> tuple[str, ...]:
    available = set(pair["a"]["signed_errors_mg_per_l"]) | set(pair["b"]["signed_errors_mg_per_l"])
    ordered = [element for element in DISPLAY_ELEMENT_ORDER if element in available]
    ordered.extend(sorted(available - set(ordered)))
    return tuple(ordered)


def _format_pair_table(pair: dict[str, Any]) -> str:
    solution_a = pair["a"]
    solution_b = pair["b"]
    targets_a = solution_a["targets_mg_per_l"]
    targets_b = solution_b["targets_mg_per_l"]
    if targets_a != targets_b:
        raise ValueError(f"Pair {pair['pair_id']} contains different A/B targets")
    lines = [
        "Alle Konzentrationen und Differenzen sind in mg/L.",
        "Positive Differenz = Ueberschuss; negative Differenz = Unterfuellung.",
        "Prozent ist nur Zusatzinformation; bei Spurenelementen besonders auf mg/L achten.",
        "",
        (
            f"{'Element':<13} {'Ziel':>10} | "
            f"{'A erreicht':>11} {'A Differenz':>12} {'A Prozent':>10} | "
            f"{'B erreicht':>11} {'B Differenz':>12} {'B Prozent':>10}"
        ),
        "-" * 99,
    ]
    for element in _ordered_pair_elements(pair):
        target = float(targets_a.get(element, 0.0))
        achieved_a = float(solution_a["achieved_mg_per_l"].get(element, 0.0))
        achieved_b = float(solution_b["achieved_mg_per_l"].get(element, 0.0))
        error_a = float(solution_a["signed_errors_mg_per_l"].get(element, achieved_a - target))
        error_b = float(solution_b["signed_errors_mg_per_l"].get(element, achieved_b - target))
        decimals = _display_decimals(target)
        label = DISPLAY_ELEMENT_NAMES.get(element, element)
        lines.append(
            f"{label:<13} {_format_decimal(target, decimals):>10} | "
            f"{_format_decimal(achieved_a, decimals):>11} "
            f"{_format_decimal(error_a, decimals, signed=True):>12} "
            f"{_format_percent(error_a, target):>10} | "
            f"{_format_decimal(achieved_b, decimals):>11} "
            f"{_format_decimal(error_b, decimals, signed=True):>12} "
            f"{_format_percent(error_b, target):>10}"
        )
    lines.extend(
        (
            "",
            f"A: Konfiguration {solution_a['config_id']}, Loesung {solution_a['solution_id']}",
            f"B: Konfiguration {solution_b['config_id']}, Loesung {solution_b['solution_id']}",
        )
    )
    return "\n".join(lines)


def label_pairs(pair_path: Path, label_path: Path, *, limit: int | None) -> int:
    pairs = _read_jsonl(pair_path)
    labels = load_labels(label_path)
    completed = 0
    for pair in pairs:
        if pair["pair_id"] in labels:
            continue
        print(f"\nProfil: {pair['profile_id']}  Paar: {pair['pair_id'][:12]}")
        print(_format_pair_table(pair))
        while True:
            choice = input("Welche Loesung ist besser? [A/B], [S] ueberspringen, [Q] beenden: ").strip().upper()
            if choice == "Q":
                return completed
            if choice in {"A", "B", "S", "SKIP"}:
                save_label(label_path, pair, "SKIP" if choice in {"S", "SKIP"} else choice)
                completed += 1
                break
        if limit is not None and completed >= limit:
            break
    return completed


def feature_names(element_order: tuple[str, ...]) -> tuple[str, ...]:
    suffixes = (
        "under_mg",
        "over_mg",
        "under_relative",
        "over_relative",
        "under_reachable",
        "over_reachable",
    )
    return tuple(f"{element}:{suffix}" for element in element_order for suffix in suffixes)


def _feature_matrix(
    solutions: list[dict[str, Any]],
    names: tuple[str, ...],
) -> np.ndarray:
    rows = []
    elements = tuple(dict.fromkeys(name.split(":", 1)[0] for name in names))
    for solution in solutions:
        values = raw_features(solution, elements)
        rows.append([float(values.get(name, 0.0)) for name in names])
    return np.array(rows, dtype=float)


def _feature_scales(values: np.ndarray) -> np.ndarray:
    scales = np.ones(values.shape[1], dtype=float)
    for column in range(values.shape[1]):
        positive = values[:, column][values[:, column] > 0.0]
        if len(positive):
            scales[column] = max(float(np.quantile(positive, 0.9)), 1e-12)
    return scales


def _transform_features(values: np.ndarray, scales: np.ndarray) -> np.ndarray:
    return np.log1p(np.divide(values, scales, out=np.zeros_like(values), where=scales > 0.0))


def _sigmoid(values: np.ndarray) -> np.ndarray:
    clipped = np.clip(values, -40.0, 40.0)
    return 1.0 / (1.0 + np.exp(-clipped))


def fit_monotone_bradley_terry(
    differences: np.ndarray,
    choices: np.ndarray,
    *,
    l1: float,
    l2: float,
    iterations: int,
    learning_rate: float,
) -> np.ndarray:
    if differences.ndim != 2 or choices.shape != (differences.shape[0],):
        raise ValueError("Invalid training matrix dimensions")
    if not len(choices):
        raise ValueError("At least one labelled pair is required")
    weights = np.full(differences.shape[1], 0.05, dtype=float)
    for iteration in range(iterations):
        probabilities = _sigmoid(differences @ weights)
        gradient = differences.T @ (probabilities - choices) / len(choices)
        gradient += l2 * weights + l1
        step = learning_rate / math.sqrt(1.0 + iteration / 100.0)
        updated = np.maximum(0.0, weights - step * gradient)
        if float(np.max(np.abs(updated - weights))) < 1e-10:
            weights = updated
            break
        weights = updated
    return weights


def _training_data(
    pairs: list[dict[str, Any]],
    labels: dict[str, dict[str, Any]],
    names: tuple[str, ...],
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    selected_pairs = []
    choices = []
    profiles = []
    for pair in pairs:
        label = labels.get(str(pair["pair_id"]))
        if label is None or label["choice"] == "SKIP":
            continue
        if label["matrix_signature"] != pair["matrix_signature"]:
            raise ValueError(f"Label signature mismatch for pair {pair['pair_id']}")
        selected_pairs.append(pair)
        choices.append(1.0 if label["choice"] == "A" else 0.0)
        profiles.append(str(pair["profile_id"]))
    if not selected_pairs:
        raise ValueError("No A/B labels are available")
    solutions = [item[side] for item in selected_pairs for side in ("a", "b")]
    raw = _feature_matrix(solutions, names)
    return raw, np.array(choices), profiles


def _classification_metrics(differences: np.ndarray, choices: np.ndarray, weights: np.ndarray) -> dict[str, float]:
    probabilities = _sigmoid(differences @ weights)
    epsilon = 1e-12
    log_loss = -float(
        np.mean(choices * np.log(probabilities + epsilon) + (1.0 - choices) * np.log(1.0 - probabilities + epsilon))
    )
    accuracy = float(np.mean((probabilities >= 0.5) == (choices >= 0.5)))
    return {"accuracy": accuracy, "log_loss": log_loss}


def train_model(
    pairs: list[dict[str, Any]],
    labels: dict[str, dict[str, Any]],
    element_order: tuple[str, ...],
    *,
    l1: float,
    l2: float,
    iterations: int,
    learning_rate: float,
) -> dict[str, Any]:
    if not pairs:
        raise ValueError("No preference pairs are available")
    signatures = {str(pair["matrix_signature"]) for pair in pairs}
    if len(signatures) != 1:
        raise ValueError("Preference pairs contain multiple matrix signatures")
    names = feature_names(element_order)
    raw, choices, profiles = _training_data(pairs, labels, names)
    scales = _feature_scales(raw)
    transformed = _transform_features(raw, scales)
    differences = transformed[1::2] - transformed[0::2]
    weights = fit_monotone_bradley_terry(
        differences,
        choices,
        l1=l1,
        l2=l2,
        iterations=iterations,
        learning_rate=learning_rate,
    )
    holdouts = []
    profile_array = np.array(profiles)
    for profile_id in sorted(set(profiles)):
        test_mask = profile_array == profile_id
        train_mask = ~test_mask
        if not np.any(train_mask) or not np.any(test_mask):
            continue
        train_solution_mask = np.repeat(train_mask, 2)
        fold_scales = _feature_scales(raw[train_solution_mask])
        fold_transformed = _transform_features(raw, fold_scales)
        fold_differences = fold_transformed[1::2] - fold_transformed[0::2]
        fold_weights = fit_monotone_bradley_terry(
            fold_differences[train_mask],
            choices[train_mask],
            l1=l1,
            l2=l2,
            iterations=iterations,
            learning_rate=learning_rate,
        )
        holdouts.append(
            {
                "profile_id": profile_id,
                "labels": int(np.count_nonzero(test_mask)),
                **_classification_metrics(fold_differences[test_mask], choices[test_mask], fold_weights),
            }
        )
    nonzero = [
        {"feature": name, "weight": float(weight)} for name, weight in zip(names, weights, strict=True) if weight > 1e-9
    ]
    nonzero.sort(key=lambda value: (-value["weight"], value["feature"]))
    profile_contexts: dict[str, dict[str, Any]] = {}
    for pair in pairs:
        spans = pair["a"].get("reachable_error_span_mg_per_l") or {}
        profile_contexts[str(pair["profile_id"])] = {
            "reachable_error_span_mg_per_l": {str(key): float(value) for key, value in spans.items()}
        }
    return {
        "schema_version": SCHEMA_VERSION,
        "matrix_signature": pairs[0]["matrix_signature"],
        "model": "projected non-negative Bradley-Terry logistic regression",
        "features": list(names),
        "scales": [float(value) for value in scales],
        "weights": [float(value) for value in weights],
        "regularization": {"l1": l1, "l2": l2},
        "training": {"labels": len(choices), **_classification_metrics(differences, choices, weights)},
        "leave_one_profile_out": holdouts,
        "nonzero_weights": nonzero,
        "profile_contexts": profile_contexts,
    }


def solution_cost(
    solution: dict[str, Any],
    model: dict[str, Any],
) -> float:
    names = tuple(model["features"])
    raw = _feature_matrix([solution], names)
    transformed = _transform_features(raw, np.array(model["scales"], dtype=float))
    return float(transformed[0] @ np.array(model["weights"], dtype=float))


def solution_penalties(
    solution: dict[str, Any],
    model: dict[str, Any],
) -> dict[str, float]:
    names = tuple(model["features"])
    raw = _feature_matrix([solution], names)
    transformed = _transform_features(raw, np.array(model["scales"], dtype=float))[0]
    contributions = transformed * np.array(model["weights"], dtype=float)
    penalties: dict[str, float] = {}
    for name, contribution in zip(names, contributions, strict=True):
        element = name.split(":", 1)[0]
        penalties[element] = penalties.get(element, 0.0) + float(contribution)
    return penalties


def rank_configurations(
    database: MatrixDatabase,
    model: dict[str, Any],
    *,
    top: int,
) -> dict[str, Any]:
    if model["matrix_signature"] != database.signature:
        raise ValueError("Model and exhaustive database signatures differ")
    database.connection.executescript(
        """
        DROP TABLE IF EXISTS temp.preference_solution_scores;
        CREATE TEMP TABLE preference_solution_scores (
            profile_id TEXT NOT NULL,
            solution_id INTEGER NOT NULL,
            total_cost REAL NOT NULL,
            worst_element_cost REAL NOT NULL,
            worst_element TEXT NOT NULL,
            PRIMARY KEY(profile_id, solution_id)
        ) WITHOUT ROWID;
        """
    )
    for profile_id in database.profile_order:
        targets = database.profiles[profile_id]["targets_mg_per_l"]
        elements = database.objective_elements(profile_id)
        target_values = {key: float(targets.get(key, 0.0)) for key in elements}
        profile_context = (model.get("profile_contexts") or {}).get(profile_id) or {}
        spans = profile_context.get("reachable_error_span_mg_per_l") or database.reachable_spans(profile_id)
        solution_rows = list(
            database.connection.execute(
                """
                SELECT DISTINCT r.solution_id, s.solution_hash, s.achieved_vector
                FROM runs AS r
                JOIN solutions AS s ON s.solution_id = r.solution_id
                WHERE r.profile_id = ? AND r.portfolio_id = ? AND r.status = 'ok'
                """,
                (profile_id, database.portfolio_id),
            )
        )
        solutions = []
        for solution_id, solution_hash, payload in solution_rows:
            achieved = _unpack_vector(payload, len(database.element_order))
            achieved_values = {key: float(achieved[database.element_index[key]]) for key in elements}
            solutions.append(
                {
                    "solution_id": int(solution_id),
                    "solution_hash": str(solution_hash),
                    "targets_mg_per_l": target_values,
                    "achieved_mg_per_l": achieved_values,
                    "signed_errors_mg_per_l": {key: achieved_values[key] - target_values[key] for key in elements},
                    "reachable_error_span_mg_per_l": spans,
                }
            )
        if solutions:
            names = tuple(model["features"])
            transformed = _transform_features(_feature_matrix(solutions, names), np.array(model["scales"], dtype=float))
            weights = np.array(model["weights"], dtype=float)
            contributions = transformed * weights
            element_names = np.array([name.split(":", 1)[0] for name in names])
            score_rows = []
            for row_index, solution in enumerate(solutions):
                by_element = {
                    element: float(contributions[row_index, element_names == element].sum()) for element in elements
                }
                worst_name, worst_value = max(by_element.items(), key=lambda item: (item[1], item[0]))
                score_rows.append(
                    (
                        profile_id,
                        int(solution["solution_id"]),
                        float(contributions[row_index].sum()),
                        worst_value,
                        worst_name,
                    )
                )
            database.connection.executemany(
                """
                INSERT INTO temp.preference_solution_scores(
                    profile_id, solution_id, total_cost, worst_element_cost, worst_element
                ) VALUES (?, ?, ?, ?, ?)
                """,
                score_rows,
            )
    ordered = list(
        database.connection.execute(
            """
            SELECT
                r.config_id,
                MAX(s.worst_element_cost) AS worst_element_cost,
                MAX(s.total_cost) AS worst_profile_cost,
                AVG(s.total_cost) AS mean_profile_cost
            FROM runs AS r
            JOIN temp.preference_solution_scores AS s
              ON s.profile_id = r.profile_id AND s.solution_id = r.solution_id
            WHERE r.portfolio_id = ? AND r.status = 'ok'
            GROUP BY r.config_id
            HAVING COUNT(*) = ?
            ORDER BY worst_element_cost, worst_profile_cost, mean_profile_cost, r.config_id
            """,
            (database.portfolio_id, len(database.profile_order)),
        )
    )
    ranking = []
    for rank, aggregate in enumerate(ordered[:top], start=1):
        config_id = int(aggregate[0])
        element_context = database.connection.execute(
            """
            SELECT s.profile_id, s.worst_element
            FROM runs AS r
            JOIN temp.preference_solution_scores AS s
              ON s.profile_id = r.profile_id AND s.solution_id = r.solution_id
            WHERE r.config_id = ? AND r.portfolio_id = ? AND r.status = 'ok'
            ORDER BY s.worst_element_cost DESC, s.profile_id, s.worst_element
            LIMIT 1
            """,
            (config_id, database.portfolio_id),
        ).fetchone()
        profile_context = database.connection.execute(
            """
            SELECT s.profile_id
            FROM runs AS r
            JOIN temp.preference_solution_scores AS s
              ON s.profile_id = r.profile_id AND s.solution_id = r.solution_id
            WHERE r.config_id = ? AND r.portfolio_id = ? AND r.status = 'ok'
            ORDER BY s.total_cost DESC, s.profile_id
            LIMIT 1
            """,
            (config_id, database.portfolio_id),
        ).fetchone()
        ranking.append(
            {
                "rank": rank,
                **database.config(config_id),
                "worst_element_cost": float(aggregate[1]),
                "worst_element": {
                    "profile_id": str(element_context[0]),
                    "element": str(element_context[1]),
                },
                "worst_profile_cost": float(aggregate[2]),
                "worst_profile_id": str(profile_context[0]),
                "mean_profile_cost": float(aggregate[3]),
            }
        )
    rank_by_config = {int(row[0]): rank for rank, row in enumerate(ordered, start=1)}
    reference_ranks = {
        str(config_id): rank_by_config[config_id] for config_id in REFERENCE_CONFIG_IDS if config_id in rank_by_config
    }
    references = {
        str(config_id): {
            "rank": rank_by_config[config_id],
            **database.config(config_id),
        }
        for config_id in REFERENCE_CONFIG_IDS
        if config_id in rank_by_config
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "matrix_signature": database.signature,
        "selection": ("lexicographic worst learned element penalty, then worst profile cost, then mean profile cost"),
        "complete_configurations": len(ordered),
        "reference_ranks": reference_ranks,
        "references": references,
        "ranking": ranking,
    }


def _add_common_database_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Learn and apply solver-result preferences without hardcoded weights.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    pairs = subparsers.add_parser("pairs", help="Generate high-conflict Pareto A/B pairs")
    _add_common_database_argument(pairs)
    pairs.add_argument("--out", type=Path, default=DEFAULT_PAIR_PATH)
    pairs.add_argument("--count", type=int, default=120)
    pairs.add_argument("--candidate-limit", type=int, default=250)
    pairs.add_argument("--seed", type=int, default=20260716)
    pairs.add_argument("--model", type=Path, default=None)
    pairs.add_argument("--labels", type=Path, default=DEFAULT_LABEL_PATH)
    pairs.add_argument("--append", action="store_true")

    label = subparsers.add_parser("label", help="Interactively label generated pairs")
    label.add_argument("--pairs", type=Path, default=DEFAULT_PAIR_PATH)
    label.add_argument("--labels", type=Path, default=DEFAULT_LABEL_PATH)
    label.add_argument("--limit", type=int, default=None)

    train = subparsers.add_parser("train", help="Train and cross-validate the monotone preference model")
    _add_common_database_argument(train)
    train.add_argument("--pairs", type=Path, default=DEFAULT_PAIR_PATH)
    train.add_argument("--labels", type=Path, default=DEFAULT_LABEL_PATH)
    train.add_argument("--out", type=Path, default=DEFAULT_MODEL_PATH)
    train.add_argument("--l1", type=float, default=0.002)
    train.add_argument("--l2", type=float, default=0.02)
    train.add_argument("--iterations", type=int, default=4_000)
    train.add_argument("--learning-rate", type=float, default=0.15)

    rank = subparsers.add_parser("rank", help="Rank complete configurations worst-element first")
    _add_common_database_argument(rank)
    rank.add_argument("--model", type=Path, default=DEFAULT_MODEL_PATH)
    rank.add_argument("--out", type=Path, default=DEFAULT_RANKING_PATH)
    rank.add_argument("--top", type=int, default=200)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "label":
        completed = label_pairs(args.pairs, args.labels, limit=args.limit)
        print(f"Stored {completed} new preference labels in {args.labels}")
        return 0

    database = MatrixDatabase(args.database)
    try:
        if args.command == "pairs":
            if args.count < 1 or args.candidate_limit < 2:
                raise ValueError("--count must be >= 1 and --candidate-limit must be >= 2")
            existing_pairs = _read_jsonl(args.out) if args.append else []
            excluded_ids = {str(pair["pair_id"]) for pair in existing_pairs}
            excluded_ids.update(load_labels(args.labels))
            model = json.loads(args.model.read_text(encoding="utf-8")) if args.model is not None else None
            pairs = generate_pairs(
                database,
                count=args.count,
                candidate_limit=args.candidate_limit,
                seed=args.seed,
                model=model,
                excluded_pair_ids=excluded_ids,
            )
            _write_jsonl(args.out, [*existing_pairs, *pairs])
            print(f"Wrote {len(pairs)} new preference pairs to {args.out} ({len(existing_pairs) + len(pairs)} total)")
        elif args.command == "train":
            pairs = _read_jsonl(args.pairs)
            labels = load_labels(args.labels)
            model = train_model(
                pairs,
                labels,
                database.element_order,
                l1=args.l1,
                l2=args.l2,
                iterations=args.iterations,
                learning_rate=args.learning_rate,
            )
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(
                json.dumps(model, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8"
            )
            print(
                f"Trained on {model['training']['labels']} labels: "
                f"accuracy={model['training']['accuracy']:.3f}, log_loss={model['training']['log_loss']:.3f}"
            )
        elif args.command == "rank":
            model = json.loads(args.model.read_text(encoding="utf-8"))
            ranking = rank_configurations(database, model, top=args.top)
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(
                json.dumps(ranking, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            print(f"Wrote top {len(ranking['ranking'])} configurations to {args.out}")
    finally:
        database.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
