from __future__ import annotations

import argparse
import json
from typing import Any


SOLVER_CONFIG_DEFINITIONS: tuple[dict[str, Any], ...] = (
    {"key": "relative_weighting", "type": "boolean", "default": False},
    {"key": "overshoot_penalty", "type": "number", "default": 1.0},
    {"key": "irls_max_outer_iter", "type": "integer", "default": 4},
    {"key": "scale_eps_mg_per_l", "type": "number", "default": 1.0},
    {"key": "singleton_supplier_enabled", "type": "boolean", "default": False},
    {"key": "singleton_share_threshold", "type": "number", "default": 0.85},
    {"key": "singleton_max_regress_pp", "type": "number", "default": 0.25},
    {"key": "singleton_underfill_enabled", "type": "boolean", "default": True},
    {"key": "singleton_underfill_share_threshold", "type": "number", "default": 0.85},
    {"key": "singleton_underfill_max_iter", "type": "integer", "default": 2},
    {"key": "nitrogen_objective_mode", "type": "string", "default": "n_total_only"},
    {"key": "n_total_governor_enabled", "type": "boolean", "default": False},
    {"key": "n_total_governor_weight", "type": "number", "default": 1.0},
)

SOLVER_CONFIG_TYPES = {definition["key"]: definition["type"] for definition in SOLVER_CONFIG_DEFINITIONS}


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
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


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

    return overrides
