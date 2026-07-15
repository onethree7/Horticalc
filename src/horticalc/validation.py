from __future__ import annotations

import math
from collections.abc import Iterable
from typing import Any


def finite_float(value: Any, location: str) -> float:
    try:
        numeric_value = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{location} must be numeric") from exc
    if not math.isfinite(numeric_value):
        raise ValueError(f"{location} must be finite")
    return numeric_value


def positive_float(value: Any, location: str) -> float:
    numeric_value = finite_float(value, location)
    if numeric_value <= 0.0:
        raise ValueError(f"{location} must be > 0 (greater than zero)")
    return numeric_value


def non_negative_float(value: Any, location: str) -> float:
    numeric_value = finite_float(value, location)
    if numeric_value < 0.0:
        raise ValueError(f"{location} must be >= 0")
    return numeric_value


def percentage_float(value: Any, location: str) -> float:
    numeric_value = finite_float(value, location)
    if not 0.0 <= numeric_value <= 100.0:
        raise ValueError(f"{location} must be between 0 and 100")
    return numeric_value


def unique_strings(values: Iterable[object], field_name: str) -> list[str]:
    normalized = [str(value) for value in values]
    seen: set[str] = set()
    duplicates: list[str] = []
    for value in normalized:
        if value in seen and value not in duplicates:
            duplicates.append(value)
        seen.add(value)
    if duplicates:
        raise ValueError(f"{field_name} must not contain duplicates: {duplicates}")
    return normalized
