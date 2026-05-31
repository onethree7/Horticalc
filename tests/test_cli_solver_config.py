from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

import horticalc.__main__ as cli
from horticalc.solver_config import SOLVER_CONFIG_DEFINITIONS


def test_solver_config_definitions_use_data_backed_defaults() -> None:
    defaults = {definition["key"]: definition["default"] for definition in SOLVER_CONFIG_DEFINITIONS}

    assert defaults["nitrogen_objective_mode"] == "n_total_only"
    assert defaults["relative_weighting"] is True
    assert defaults["macro_priority_enabled"] is False
    assert defaults["stage_optimization_enabled"] is False


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
