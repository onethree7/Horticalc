from pathlib import Path


def test_solver_ui_uses_reduced_solver_config_controls() -> None:
    index_html = Path(__file__).resolve().parents[1] / "frontend" / "index.html"
    app_js = Path(__file__).resolve().parents[1] / "frontend" / "app.js"
    html_content = index_html.read_text(encoding="utf-8")
    js_content = app_js.read_text(encoding="utf-8")

    expected_controls = [
        "solverConfigRelativeWeighting",
        "solverConfigNitrogenObjectiveMode",
        "solverConfigOvershootPenalty",
        "solverConfigSingletonSupplierEnabled",
        "solverConfigSingletonUnderfillEnabled",
        "solverConfigNTotalGovernorEnabled",
    ]
    for control_id in expected_controls:
        assert f'id="{control_id}"' in html_content

    assert "macro_priority_enabled" not in js_content
    assert "stage_optimization_enabled" not in js_content
    assert "solverConfigMacroPriorityEnabled" not in html_content
    assert "solverConfigStageOptimizationEnabled" not in html_content


def test_solver_ui_fetches_backend_solver_config_schema() -> None:
    app_js = Path(__file__).resolve().parents[1] / "frontend" / "app.js"
    content = app_js.read_text(encoding="utf-8")

    assert "/schema/solver-config" in content
    assert "fetchSolverConfigDefinitions" in content
    assert "normalizeSolverConfigDefinitions" in content


def test_solver_ui_exposes_nitrogen_objective_checkbox() -> None:
    index_html = Path(__file__).resolve().parents[1] / "frontend" / "index.html"
    app_js = Path(__file__).resolve().parents[1] / "frontend" / "app.js"
    html_content = index_html.read_text(encoding="utf-8")
    js_content = app_js.read_text(encoding="utf-8")

    assert 'id="solverConfigNitrogenObjectiveMode"' in html_content
    assert "N-total statt N-Formen" in html_content
    assert "nitrogen_objective_mode" in js_content
    assert "n_total_only" in js_content
    assert "n_forms_only" in js_content


def test_solver_advanced_config_lives_in_solver_panel() -> None:
    index_html = Path(__file__).resolve().parents[1] / "frontend" / "index.html"
    html_content = index_html.read_text(encoding="utf-8")

    assert 'class="rail-advanced-config"' not in html_content
    assert 'class="solver-advanced-config"' in html_content
    assert html_content.index('id="solverMode"') < html_content.index('id="solverConfigResetDefaults"')
    assert html_content.index('class="solver-advanced-config"') < html_content.index('id="solverUreaToggle"')
    assert html_content.index('class="solver-advanced-config"') < html_content.index('id="solverPhosphate"')
    assert html_content.index('id="solverTargetsResultsTable"') < html_content.index('class="solver-advanced-config"')


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
