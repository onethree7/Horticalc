from pathlib import Path


def test_solver_ui_hides_legacy_macro_and_stage_controls() -> None:
    index_html = Path(__file__).resolve().parents[1] / "frontend" / "index.html"
    content = index_html.read_text(encoding="utf-8")

    assert "Macro priority" not in content
    assert "Stage optimization" not in content
    assert 'id="solverConfigMacroPriorityEnabled"' not in content
    assert 'id="solverConfigStageOptimizationEnabled"' not in content


def test_solver_ui_fetches_backend_solver_config_schema() -> None:
    app_js = Path(__file__).resolve().parents[1] / "frontend" / "app.js"
    content = app_js.read_text(encoding="utf-8")

    assert "/schema/solver-config" in content
    assert "fetchSolverConfigDefinitions" in content
    assert "normalizeSolverConfigDefinitions" in content


def test_solver_ui_does_not_restore_hidden_solver_config_from_saved_solution() -> None:
    app_js = Path(__file__).resolve().parents[1] / "frontend" / "app.js"
    content = app_js.read_text(encoding="utf-8")

    assert "applySolverConfig(savedSolution.solver_config || {})" not in content


def test_solver_ui_does_not_auto_apply_recipe_solver_config() -> None:
    app_js = Path(__file__).resolve().parents[1] / "frontend" / "app.js"
    content = app_js.read_text(encoding="utf-8")

    assert "if (recipe?.solver_config)" not in content
    assert "applySolverConfig(recipe.solver_config)" not in content


def test_solver_ui_does_not_persist_solver_config_in_recipe_or_snapshot() -> None:
    app_js = Path(__file__).resolve().parents[1] / "frontend" / "app.js"
    content = app_js.read_text(encoding="utf-8")

    build_recipe_block = content.split("function buildRecipePayload(", 1)[1].split("function buildRecipePayloadFromSelection", 1)[0]
    build_snapshot_block = content.split("function buildSolutionSnapshot()", 1)[1].split("function restoreSolverAllowedFromStorage", 1)[0]

    assert "solver_config" not in build_recipe_block
    assert "solver_config" not in build_snapshot_block
