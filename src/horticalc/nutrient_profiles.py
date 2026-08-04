from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .chemistry import ALLOWED_TARGET_KEYS
from .solver_config import validate_solver_config
from .validation import non_negative_float, percentage_float, positive_float, unique_strings

NUTRIENT_SOLUTION_SETUP_FIELDS = frozenset(
    {
        "liters",
        "water_profile",
        "osmosis_percent",
        "fertilizers_allowed",
        "fixed_grams",
        "urea_as_nh4",
        "solver_config",
    }
)


def _field_location(location: str, field: str) -> str:
    return f"{location}: {field}" if location else field


def _non_negative_mapping(value: Any, *, location: str, allowed_keys: set[str] | None = None) -> dict[str, float]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{location} must be a mapping")
    result: dict[str, float] = {}
    for raw_key, raw_value in value.items():
        key = str(raw_key).strip()
        if not key:
            raise ValueError(f"{location} must contain non-empty keys")
        if key in result:
            raise ValueError(f"{location} must not contain duplicate normalized keys: {key}")
        if allowed_keys is not None and key not in allowed_keys:
            raise ValueError(f"Invalid target key: {key}")
        result[key] = non_negative_float(raw_value, f"{location}.{key}")
    return result


def _fertilizer_names(value: Any, *, location: str) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"{location} must be a list")
    names = [str(entry).strip() for entry in value]
    if any(not name for name in names):
        raise ValueError(f"{location} must contain non-empty names")
    return unique_strings(names, location)


def normalize_nutrient_solution_data(
    value: Mapping[str, Any],
    *,
    location: str = "",
    fallback_name: str | None = None,
) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{location or 'Nutrient solution'} must be a mapping")

    raw_name = value.get("name") or fallback_name
    if not isinstance(raw_name, str) or not raw_name.strip():
        raise ValueError(f"{_field_location(location, 'name')} must be a non-empty string")
    raw_source = value.get("source")
    if raw_source is not None and not isinstance(raw_source, str):
        raise ValueError(f"{_field_location(location, 'source')} must be a string")

    targets_location = _field_location(location, "targets_mg_per_l")
    result: dict[str, Any] = {
        "name": raw_name.strip(),
        "source": raw_source or "",
        "targets_mg_per_l": _non_negative_mapping(
            value.get("targets_mg_per_l", {}),
            location=targets_location,
            allowed_keys=set(ALLOWED_TARGET_KEYS),
        ),
    }

    if "liters" in value:
        result["liters"] = positive_float(value["liters"], _field_location(location, "liters"))
    if "water_profile" in value:
        water_profile = value["water_profile"]
        if not isinstance(water_profile, str) or not water_profile.strip():
            raise ValueError(f"{_field_location(location, 'water_profile')} must be a non-empty string")
        result["water_profile"] = water_profile.strip()
    if "osmosis_percent" in value:
        result["osmosis_percent"] = percentage_float(
            value["osmosis_percent"],
            _field_location(location, "osmosis_percent"),
        )

    fertilizers_allowed: list[str] | None = None
    if "fertilizers_allowed" in value:
        fertilizers_allowed = _fertilizer_names(
            value["fertilizers_allowed"],
            location=_field_location(location, "fertilizers_allowed"),
        )
        result["fertilizers_allowed"] = fertilizers_allowed
    if "fixed_grams" in value:
        fixed_grams = _non_negative_mapping(
            value["fixed_grams"],
            location=_field_location(location, "fixed_grams"),
        )
        outside_allowed = sorted(set(fixed_grams) - set(fertilizers_allowed or []))
        if outside_allowed:
            raise ValueError(
                f"{_field_location(location, 'fixed_grams')} not in fertilizers_allowed: {outside_allowed}"
            )
        result["fixed_grams"] = fixed_grams
    if "urea_as_nh4" in value:
        if not isinstance(value["urea_as_nh4"], bool):
            raise ValueError(f"{_field_location(location, 'urea_as_nh4')} must be a boolean")
        result["urea_as_nh4"] = value["urea_as_nh4"]
    if "solver_config" in value:
        result["solver_config"] = validate_solver_config(value["solver_config"] or {})
    return result


def nutrient_solution_has_setup(value: Mapping[str, Any]) -> bool:
    return any(field in value for field in NUTRIENT_SOLUTION_SETUP_FIELDS)
