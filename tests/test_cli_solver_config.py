from __future__ import annotations

import json
from pathlib import Path

import pytest

import horticalc.__main__ as cli
from horticalc.solver_config import (
    MAX_IRLS_MAX_OUTER_ITER,
    MAX_SINGLETON_UNDERFILL_MAX_ITER,
    SOLVER_CONFIG_DEFAULTS,
    SOLVER_CONFIG_DEFINITIONS,
    resolve_solver_config,
    validate_solver_config,
)

def test_solver_config_definitions_use_data_backed_defaults() -> None:
    defaults = {definition["key"]: definition["default"] for definition in SOLVER_CONFIG_DEFINITIONS}

    assert defaults["nitrogen_objective_mode"] == "n_total_only"
    assert defaults["relative_weighting"] is False
    assert defaults["singleton_supplier_enabled"] is False
    assert defaults["singleton_underfill_enabled"] is True
    assert defaults["n_form_priority_weights"] == {}
    assert defaults["irls_max_outer_iter"] <= MAX_IRLS_MAX_OUTER_ITER
    assert defaults["singleton_underfill_max_iter"] <= MAX_SINGLETON_UNDERFILL_MAX_ITER
    nitrogen_definition = next(
        definition
        for definition in SOLVER_CONFIG_DEFINITIONS
        if definition["key"] == "nitrogen_objective_mode"
    )
    assert nitrogen_definition["choices"] == ["as_targets", "n_total_only", "n_forms_only"]
    assert next(
        definition for definition in SOLVER_CONFIG_DEFINITIONS if definition["key"] == "irls_max_outer_iter"
    )["maximum"] == MAX_IRLS_MAX_OUTER_ITER
    assert next(
        definition
        for definition in SOLVER_CONFIG_DEFINITIONS
        if definition["key"] == "singleton_underfill_max_iter"
    )["maximum"] == MAX_SINGLETON_UNDERFILL_MAX_ITER
    assert "macro_priority_enabled" not in defaults
    assert "stage_optimization_enabled" not in defaults

def test_solve_cli_passes_solver_config_overrides(monkeypatch, capsys, tmp_path) -> None:
    recipe_path = tmp_path / "recipe.yml"
    recipe_path.write_text("targets: {}\n", encoding="utf-8")
    captured = {}

    def fake_solve_recipe(recipe_path_arg, *, water_profile_path=None, solver_config_overrides=None):
        captured["recipe_path"] = recipe_path_arg
        captured["water_profile_path"] = water_profile_path
        captured["solver_config_overrides"] = solver_config_overrides
        return {"ok": True}

    monkeypatch.setattr(cli, "resolve_recipe_path", lambda value: Path(value))
    monkeypatch.setattr(cli, "solve_recipe", fake_solve_recipe)

    cli.main(
        [
            "solve",
            str(recipe_path),
            "--no-relative-weighting",
            "--overshoot-penalty",
            "1.5",
            "--n-total-governor-enabled",
            "--n-total-governor-weight",
            "0.05",
            "--nitrogen-objective-mode",
            "n_forms_only",
            "--solver-config",
            "n_form_priority_weights={\"N_NO3\": 3.0}",
        ]
    )

    assert json.loads(capsys.readouterr().out) == {"ok": True}
    assert captured["recipe_path"] == recipe_path
    assert captured["water_profile_path"] is None
    assert captured["solver_config_overrides"] == {
        "relative_weighting": False,
        "overshoot_penalty": 1.5,
        "n_total_governor_enabled": True,
        "n_total_governor_weight": 0.05,
        "nitrogen_objective_mode": "n_forms_only",
        "n_form_priority_weights": {"N_NO3": 3.0},
    }

def test_solve_cli_keeps_solver_config_optional(monkeypatch, capsys, tmp_path) -> None:
    recipe_path = tmp_path / "recipe.yml"
    recipe_path.write_text("targets: {}\n", encoding="utf-8")
    captured = {}

    def fake_solve_recipe(recipe_path_arg, *, water_profile_path=None, solver_config_overrides=None):
        captured["solver_config_overrides"] = solver_config_overrides
        return {"ok": True}

    monkeypatch.setattr(cli, "resolve_recipe_path", lambda value: Path(value))
    monkeypatch.setattr(cli, "solve_recipe", fake_solve_recipe)

    cli.main(["solve", str(recipe_path)])

    assert json.loads(capsys.readouterr().out) == {"ok": True}
    assert captured["solver_config_overrides"] == {}

def test_solve_cli_rejects_non_object_solver_config_json(capsys, tmp_path) -> None:
    recipe_path = tmp_path / "recipe.yml"
    recipe_path.write_text("targets: {}\n", encoding="utf-8")

    with pytest.raises(SystemExit) as exc_info:
        cli.main(["solve", str(recipe_path), "--solver-config-json", "[]"])

    assert exc_info.value.code == 2
    assert "--solver-config-json must be a JSON object" in capsys.readouterr().err


def test_cli_help_uses_english_for_common_arguments(capsys) -> None:
    with pytest.raises(SystemExit) as exc_info:
        cli.main(["--help"])

    assert exc_info.value.code == 0
    help_text = capsys.readouterr().out
    assert "load a recipe file explicitly" in help_text
    assert "water profile file" in help_text
    assert "Pretty-print the JSON output" in help_text


def test_solver_config_validation_preserves_valid_partial_values() -> None:
    config = {
        "relative_weighting": True,
        "overshoot_penalty": 1,
        "n_form_priority_weights": {"N_NO3": 3.0},
    }

    assert validate_solver_config(config) == config
    resolved = resolve_solver_config(config)
    assert resolved["relative_weighting"] is True
    assert resolved["overshoot_penalty"] == 1
    assert resolved["n_form_priority_weights"] == {"N_NO3": 3.0}
    assert set(resolved) == set(SOLVER_CONFIG_DEFAULTS)


@pytest.mark.parametrize(
    "config, message",
    [
        ({"mystery": True}, "Unknown solver config key"),
        ({"relative_weighting": "false"}, "Invalid solver config value"),
        ({"irls_max_outer_iter": 1.9}, "Invalid solver config value"),
        (
            {"irls_max_outer_iter": MAX_IRLS_MAX_OUTER_ITER + 1},
            f"Invalid solver config value: irls_max_outer_iter must be <= {MAX_IRLS_MAX_OUTER_ITER}",
        ),
        ({"overshoot_penalty": float("nan")}, "Invalid solver config value"),
        ({"nitrogen_objective_mode": "chaos_mode"}, "Invalid solver config value"),
        (
            {"singleton_underfill_max_iter": MAX_SINGLETON_UNDERFILL_MAX_ITER + 1},
            "Invalid solver config value: singleton_underfill_max_iter must be <=",
        ),
        ({"n_form_priority_weights": {"K": 2.0}}, "Invalid n_form_priority_weights key"),
        ({"n_form_priority_weights": {"N_NO3": -1.0}}, "Invalid n_form_priority_weights value"),
    ],
)
def test_solver_config_validation_rejects_invalid_values(config: dict, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        validate_solver_config(config)
