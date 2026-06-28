from tests.frontend_assets import read_frontend_file


def test_solver_ui_uses_reduced_solver_config_controls() -> None:
    html_content = read_frontend_file("index.html")
    js_content = read_frontend_file("app.js")

    expected_controls = [
        "solverConfigRelativeWeighting",
        "solverConfigNitrogenObjectiveMode",
        "solverConfigSObjectiveEnabled",
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
    content = read_frontend_file("app.js")

    assert "/schema/solver-config" in content
    assert "fetchSolverConfigDefinitions" in content
    assert "normalizeSolverConfigDefinitions" in content

def test_solver_ui_exposes_nitrogen_objective_checkbox() -> None:
    html_content = read_frontend_file("index.html")
    js_content = read_frontend_file("app.js")

    assert 'id="solverConfigNitrogenObjectiveMode"' in html_content
    assert "N-total statt N-Formen" in html_content
    assert "nitrogen_objective_mode" in js_content
    assert "n_total_only" in js_content
    assert "n_forms_only" in js_content

def test_solver_ui_exposes_s_objective_toggle() -> None:
    html_content = read_frontend_file("index.html")
    js_content = read_frontend_file("app.js")

    assert 'id="solverConfigSObjectiveEnabled"' in html_content
    assert 'data-i18n="solver.sAsTarget"' in html_content
    assert "s_objective_enabled" in js_content

def test_solver_ui_merges_local_solver_config_fallbacks() -> None:
    content = read_frontend_file("app.js")

    assert "FALLBACK_SOLVER_CONFIG_DEFINITIONS.forEach" in content
    assert "normalized.push({ ...definition })" in content

def test_solver_advanced_config_lives_in_solver_panel() -> None:
    html_content = read_frontend_file("index.html")

    assert 'class="rail-advanced-config"' not in html_content
    assert 'class="solver-advanced-config"' in html_content
    assert html_content.index('id="solverMode"') < html_content.index('id="solverConfigResetDefaults"')
    assert html_content.index('class="solver-advanced-config"') < html_content.index('id="solverUreaToggle"')
    assert html_content.index('class="solver-advanced-config"') < html_content.index('id="solverPhosphate"')
    assert html_content.index('id="solverTargetsResultsTable"') < html_content.index('class="solver-advanced-config"')
    assert 'data-i18n="solver.resetConfig"' in html_content


def test_solver_config_reset_clears_persisted_overrides() -> None:
    js_content = read_frontend_file("app.js")
    reset_block = js_content.split("if (solverConfigResetDefaultsButton)", 1)[1].split(
        "[solverUreaToggle, solverPhosphateSelect]",
        1,
    )[0]

    assert "applySolverConfig();" in reset_block
    assert "renderSolverResults(null);" in reset_block
    assert "persistPreferences({ solver_config: {} });" in reset_block
    assert 'setSolverApplyStatus(t("solver.configResetDone"));' in reset_block

def test_solver_ui_does_not_restore_hidden_solver_config_from_saved_solution() -> None:
    content = read_frontend_file("app.js")

    assert "applySolverConfig(savedSolution.solver_config || {})" not in content

def test_solver_ui_applies_explicit_recipe_solver_config_without_persisting_it() -> None:
    content = read_frontend_file("app.js")

    assert "if (recipe?.solver_config && Object.keys(recipe.solver_config).length)" in content
    assert "applySolverConfig({ ...buildSolverConfigPayload(), ...recipe.solver_config })" in content

def test_solver_ui_does_not_persist_solver_config_in_recipe_or_snapshot() -> None:
    content = read_frontend_file("app.js")

    build_recipe_block = content.split("function buildRecipePayload(", 1)[1].split(
        "function buildRecipePayloadFromSelection",
        1,
    )[0]
    build_snapshot_block = content.split("function buildSolutionSnapshot()", 1)[1].split(
        "function restoreSolverAllowedFromStorage",
        1,
    )[0]

    assert "solver_config" not in build_recipe_block
    assert "solver_config" not in build_snapshot_block
