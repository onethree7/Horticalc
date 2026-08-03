from __future__ import annotations

import argparse
import json
import math
from collections.abc import Mapping
from copy import deepcopy
from typing import Any

from .chemistry import ALLOWED_TARGET_KEYS, N_FORM_KEYS

NITROGEN_OBJECTIVE_MODES = ("as_targets", "n_total_only", "n_forms_only")
SOLVER_MODELS = ("mass_nnls", "hierarchical", "legacy")
TARGET_PRIORITY_DIRECTIONS = ("under", "over")
MIN_TARGET_PRIORITY = 0
MAX_TARGET_PRIORITY = 4
DEFAULT_TARGET_PRIORITY = 3
MAX_IRLS_MAX_OUTER_ITER = 12
MAX_SINGLETON_UNDERFILL_MAX_ITER = 8

SOLVER_CONFIG_DEFINITIONS: tuple[dict[str, Any], ...] = (
    {
        "key": "solver_model",
        "type": "string",
        "default": "legacy",
        "choices": list(SOLVER_MODELS),
    },
    {
        "key": "ignored_elements",
        "type": "string_list",
        "default": [],
        "choices": sorted(ALLOWED_TARGET_KEYS),
    },
    {
        "key": "target_priorities",
        "type": "priority_mapping",
        "default": {},
        "priority_minimum": MIN_TARGET_PRIORITY,
        "priority_maximum": MAX_TARGET_PRIORITY,
        "priority_default": DEFAULT_TARGET_PRIORITY,
        "choices": sorted(ALLOWED_TARGET_KEYS),
    },
    {"key": "relative_weighting", "type": "boolean", "default": False},
    {"key": "overshoot_penalty", "type": "number", "default": 1.0, "minimum": 0.0},
    {
        "key": "irls_max_outer_iter",
        "type": "integer",
        "default": 4,
        "minimum": 1,
        "maximum": MAX_IRLS_MAX_OUTER_ITER,
    },
    {
        "key": "scale_eps_mg_per_l",
        "type": "number",
        "default": 1.0,
        "exclusive_minimum": 0.0,
    },
    {"key": "singleton_supplier_enabled", "type": "boolean", "default": False},
    {
        "key": "singleton_share_threshold",
        "type": "number",
        "default": 0.85,
        "minimum": 0.0,
        "maximum": 1.0,
    },
    {
        "key": "singleton_max_regress_pp",
        "type": "number",
        "default": 0.25,
        "minimum": 0.0,
    },
    {"key": "singleton_underfill_enabled", "type": "boolean", "default": True},
    {
        "key": "singleton_underfill_share_threshold",
        "type": "number",
        "default": 0.85,
        "minimum": 0.0,
        "maximum": 1.0,
    },
    {
        "key": "singleton_underfill_max_iter",
        "type": "integer",
        "default": 2,
        "minimum": 1,
        "maximum": MAX_SINGLETON_UNDERFILL_MAX_ITER,
    },
    {
        "key": "nitrogen_objective_mode",
        "type": "string",
        "default": "n_total_only",
        "choices": list(NITROGEN_OBJECTIVE_MODES),
    },
    {"key": "s_objective_enabled", "type": "boolean", "default": False},
    {"key": "n_total_governor_enabled", "type": "boolean", "default": False},
    {
        "key": "n_total_governor_weight",
        "type": "number",
        "default": 1.0,
        "minimum": 0.0,
    },
    {"key": "n_form_priority_weights", "type": "mapping", "default": {}, "ui": False},
)

SOLVER_CONFIG_TYPES = {definition["key"]: definition["type"] for definition in SOLVER_CONFIG_DEFINITIONS}
SOLVER_CONFIG_DEFAULTS = {definition["key"]: definition.get("default") for definition in SOLVER_CONFIG_DEFINITIONS}
SOLVER_CONFIG_BY_KEY = {definition["key"]: definition for definition in SOLVER_CONFIG_DEFINITIONS}
BOOLEAN_SOLVER_KEYS = tuple(
    definition["key"] for definition in SOLVER_CONFIG_DEFINITIONS if definition["type"] == "boolean"
)
BOOLEAN_SOLVER_DEFAULTS = {key: bool(SOLVER_CONFIG_DEFAULTS[key]) for key in BOOLEAN_SOLVER_KEYS}
MATRIX_BOOLEAN_SOLVER_KEYS = tuple(key for key in BOOLEAN_SOLVER_KEYS if key != "s_objective_enabled")
MATRIX_BOOLEAN_SOLVER_DEFAULTS = {key: BOOLEAN_SOLVER_DEFAULTS[key] for key in MATRIX_BOOLEAN_SOLVER_KEYS}


def _flag_name(key: str) -> str:
    return f"--{key.replace('_', '-')}"


def add_solver_config_arguments(parser: argparse.ArgumentParser) -> None:
    group = parser.add_argument_group("solver advanced configuration")
    for definition in SOLVER_CONFIG_DEFINITIONS:
        key = definition["key"]
        flag = _flag_name(key)
        if definition["type"] == "boolean":
            group.add_argument(
                flag,
                dest=key,
                action=argparse.BooleanOptionalAction,
                default=None,
                help=f"Override solver_config.{key}",
            )
        elif definition["type"] in ("integer", "number"):
            value_type = int if definition["type"] == "integer" else float
            group.add_argument(
                flag,
                dest=key,
                type=value_type,
                default=None,
                help=f"Override solver_config.{key}",
            )
        elif definition["type"] in {"mapping", "priority_mapping", "string_list"}:
            continue
        else:
            group.add_argument(
                flag,
                dest=key,
                default=None,
                help=f"Override solver_config.{key}",
            )
    group.add_argument(
        "--solver-config",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Override any solver_config key; may be repeated. Values are parsed as JSON when possible.",
    )
    group.add_argument(
        "--solver-config-json",
        default=None,
        metavar="JSON",
        help="Merge a JSON object into solver_config before explicit KEY=VALUE overrides.",
    )


def _parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"Expected boolean value, got {value!r}")


def _coerce_solver_config_value(key: str, value: Any) -> Any:
    value_type = SOLVER_CONFIG_TYPES.get(key)
    if value_type == "boolean":
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return _parse_bool(value)
        return bool(value)
    if value_type == "integer":
        return int(value)
    if value_type == "number":
        return float(value)
    if value_type == "string":
        return str(value)
    if value_type in {"mapping", "priority_mapping"}:
        parsed = json.loads(value) if isinstance(value, str) else value
        if not isinstance(parsed, dict):
            raise ValueError(f"Expected object value for {key}, got {value!r}")
        return parsed
    if value_type == "string_list":
        parsed = json.loads(value) if isinstance(value, str) else value
        if not isinstance(parsed, list):
            raise ValueError(f"Expected array value for {key}, got {value!r}")
        return parsed
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def validate_solver_config(
    values: Mapping[str, Any] | None,
    *,
    allow_advanced: bool = True,
) -> dict[str, Any]:
    if values is None:
        return {}
    if not isinstance(values, Mapping):
        raise ValueError("solver_config must be an object")

    validated: dict[str, Any] = {}
    for key, value in values.items():
        if not isinstance(key, str) or key not in SOLVER_CONFIG_TYPES:
            raise ValueError(f"Unknown solver config key: {key}")
        definition = SOLVER_CONFIG_BY_KEY[key]
        if not allow_advanced and not definition.get("ui", True):
            raise ValueError(f"Advanced solver config key is not accepted here: {key}")

        value_type = SOLVER_CONFIG_TYPES[key]
        if value_type == "boolean":
            if not isinstance(value, bool):
                raise ValueError(f"Invalid solver config value: {key}")
        elif value_type == "integer":
            if not isinstance(value, int) or isinstance(value, bool):
                raise ValueError(f"Invalid solver config value: {key}")
        elif value_type == "number":
            if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value):
                raise ValueError(f"Invalid solver config value: {key}")
        elif value_type == "string":
            if not isinstance(value, str):
                raise ValueError(f"Invalid solver config value: {key}")
            choices = definition.get("choices")
            if choices is not None and value not in choices:
                raise ValueError(f"Invalid solver config value: {key}")
        elif value_type == "mapping":
            if key != "n_form_priority_weights" or not isinstance(value, Mapping):
                raise ValueError(f"Invalid solver config value: {key}")
            weights: dict[str, int | float] = {}
            for form_key, weight in value.items():
                if form_key not in N_FORM_KEYS:
                    raise ValueError(f"Invalid n_form_priority_weights key: {form_key}")
                if (
                    not isinstance(weight, (int, float))
                    or isinstance(weight, bool)
                    or not math.isfinite(weight)
                    or weight < 0
                ):
                    raise ValueError(f"Invalid n_form_priority_weights value: {form_key}")
                weights[form_key] = weight
            value = weights
        elif value_type == "priority_mapping":
            if not isinstance(value, Mapping):
                raise ValueError(f"Invalid solver config value: {key}")
            priorities: dict[str, dict[str, int]] = {}
            for element, direction_values in value.items():
                if element not in ALLOWED_TARGET_KEYS:
                    raise ValueError(f"Invalid target_priorities key: {element}")
                if not isinstance(direction_values, Mapping) or not direction_values:
                    raise ValueError(f"Invalid target_priorities value: {element}")
                unknown_directions = set(direction_values) - set(TARGET_PRIORITY_DIRECTIONS)
                if unknown_directions:
                    raise ValueError(f"Invalid target_priorities direction: {element}")
                validated_directions: dict[str, int] = {}
                for direction, priority in direction_values.items():
                    if (
                        not isinstance(priority, int)
                        or isinstance(priority, bool)
                        or priority < MIN_TARGET_PRIORITY
                        or priority > MAX_TARGET_PRIORITY
                    ):
                        raise ValueError(f"Invalid target_priorities value: {element}.{direction}")
                    validated_directions[direction] = priority
                priorities[element] = validated_directions
            value = priorities
        elif value_type == "string_list":
            if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
                raise ValueError(f"Invalid solver config value: {key}")
            choices = set(definition.get("choices") or [])
            if len(value) != len(set(value)) or any(item not in choices for item in value):
                raise ValueError(f"Invalid solver config value: {key}")
            value = list(value)

        if value_type in {"integer", "number"}:
            minimum = definition.get("minimum")
            maximum = definition.get("maximum")
            exclusive_minimum = definition.get("exclusive_minimum")
            if minimum is not None and value < minimum:
                raise ValueError(f"Invalid solver config value: {key} must be >= {minimum}")
            if maximum is not None and value > maximum:
                raise ValueError(f"Invalid solver config value: {key} must be <= {maximum}")
            if exclusive_minimum is not None and value <= exclusive_minimum:
                raise ValueError(f"Invalid solver config value: {key} must be > {exclusive_minimum}")
        validated[key] = value
    return validated


def resolve_solver_config(values: Mapping[str, Any] | None) -> dict[str, Any]:
    resolved = deepcopy(SOLVER_CONFIG_DEFAULTS)
    resolved.update(validate_solver_config(values))
    return resolved


def solver_config_overrides_from_args(args: argparse.Namespace) -> dict[str, Any]:
    overrides: dict[str, Any] = {}
    json_payload = getattr(args, "solver_config_json", None)
    if json_payload:
        parsed = json.loads(json_payload)
        if not isinstance(parsed, dict):
            raise ValueError("--solver-config-json must be a JSON object")
        overrides.update(parsed)

    for definition in SOLVER_CONFIG_DEFINITIONS:
        key = definition["key"]
        value = getattr(args, key, None)
        if value is not None:
            overrides[key] = value

    for entry in getattr(args, "solver_config", []) or []:
        if "=" not in entry:
            raise ValueError("--solver-config entries must use KEY=VALUE")
        key, value = entry.split("=", 1)
        key = key.strip()
        if not key:
            raise ValueError("--solver-config entries must include a non-empty key")
        overrides[key] = _coerce_solver_config_value(key, value.strip())

    return validate_solver_config(overrides)
