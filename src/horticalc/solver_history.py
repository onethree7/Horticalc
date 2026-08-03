from __future__ import annotations

import json
import logging
import os
import tempfile
import threading
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_SOLVER_HISTORY_LIMIT = 1000
MAX_SOLVER_HISTORY_LIMIT = 10000
SOLVER_HISTORY_SCHEMA_VERSION = 1

_history_lock = threading.RLock()


def _atomic_write_entries(path: Path, entries: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            delete=False,
            dir=path.parent,
            prefix=f".{path.name}.tmp-",
        ) as temp_file:
            temp_path = Path(temp_file.name)
            for entry in entries:
                temp_file.write(json.dumps(entry, ensure_ascii=False, allow_nan=False, separators=(",", ":")))
                temp_file.write("\n")
            temp_file.flush()
            os.fsync(temp_file.fileno())
        os.replace(temp_path, path)
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def _valid_entry(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and value.get("schema_version") == SOLVER_HISTORY_SCHEMA_VERSION
        and isinstance(value.get("id"), str)
        and bool(value["id"])
        and isinstance(value.get("created_at"), str)
    )


def _read_entries_unlocked(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    entries: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        logger.warning("Unable to read solver history %s: %s", path, exc)
        return []
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError as exc:
            logger.warning("Skipping invalid solver history line %s:%s: %s", path, line_number, exc)
            continue
        if not _valid_entry(entry):
            logger.warning("Skipping invalid solver history entry %s:%s", path, line_number)
            continue
        entries.append(entry)
    return entries


def load_solver_history(path: Path) -> list[dict[str, Any]]:
    with _history_lock:
        return _read_entries_unlocked(path)


def append_solver_history(path: Path, entry: dict[str, Any], limit: int) -> None:
    if not _valid_entry(entry):
        raise ValueError("Invalid solver history entry")
    if limit < 0 or limit > MAX_SOLVER_HISTORY_LIMIT:
        raise ValueError("Invalid solver history limit")
    with _history_lock:
        if limit == 0:
            path.unlink(missing_ok=True)
            return
        entries = _read_entries_unlocked(path)
        entries.append(entry)
        _atomic_write_entries(path, entries[-limit:])


def trim_solver_history(path: Path, limit: int) -> int:
    if limit < 0 or limit > MAX_SOLVER_HISTORY_LIMIT:
        raise ValueError("Invalid solver history limit")
    with _history_lock:
        entries = _read_entries_unlocked(path)
        if limit == 0:
            path.unlink(missing_ok=True)
            return 0
        retained = entries[-limit:]
        if retained != entries:
            _atomic_write_entries(path, retained)
        return len(retained)


def clear_solver_history(path: Path) -> None:
    with _history_lock:
        path.unlink(missing_ok=True)


def solver_history_summaries(path: Path) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for entry in reversed(load_solver_history(path)):
        setup = entry.get("setup") if isinstance(entry.get("setup"), dict) else {}
        result = entry.get("result") if isinstance(entry.get("result"), dict) else {}
        targets = result.get("targets_mg_per_l") if isinstance(result.get("targets_mg_per_l"), dict) else {}
        nitrogen_target = targets.get("N_total")
        if nitrogen_target is None:
            nitrogen_target = sum(float(targets.get(key, 0) or 0) for key in ("N_NO3", "N_NH4", "N_UREA"))
        summaries.append(
            {
                "id": entry["id"],
                "created_at": entry["created_at"],
                "liters": result.get("liters", setup.get("liters", 0)),
                "solver_model": result.get("solver_model", ""),
                "targets_mg_per_l": {
                    "N_total": nitrogen_target,
                    "P": targets.get("P", 0),
                    "K": targets.get("K", 0),
                },
                "fertilizer_count": len(result.get("fertilizers") or []),
            }
        )
    return summaries


def solver_history_entry(path: Path, entry_id: str) -> dict[str, Any] | None:
    return next((entry for entry in reversed(load_solver_history(path)) if entry["id"] == entry_id), None)
