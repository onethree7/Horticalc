from tests.frontend_assets import read_frontend_file


def test_solver_ui_uses_reduced_solver_config_controls() -> None:
    html = read_frontend_file("index.html")
    solver = read_frontend_file("app/solver.js")
    for control_id in (
        "solverConfigRelativeWeighting",
        "solverConfigNitrogenObjectiveMode",
        "solverConfigSObjectiveEnabled",
        "solverConfigOvershootPenalty",
        "solverConfigSingletonSupplierEnabled",
        "solverConfigSingletonUnderfillEnabled",
        "solverConfigNTotalGovernorEnabled",
    ):
        assert f'id="{control_id}"' in html
    assert "macro_priority_enabled" not in solver
    assert "stage_optimization_enabled" not in solver


def test_solver_schema_transport_and_normalization_are_separate() -> None:
    api = read_frontend_file("app/api.js")
    solver = read_frontend_file("app/solver.js")
    main = read_frontend_file("app/main.js")
    assert 'getJson("/schema/solver-config"' in api
    assert "function normalizeSolverConfigDefinitions" in solver
    assert "api.fetchSolverConfigDefinitions(" in main


def test_solver_ui_exposes_supported_objective_controls() -> None:
    html = read_frontend_file("index.html")
    solver = read_frontend_file("app/solver.js")
    constants = read_frontend_file("app/constants.js")
    assert 'id="solverConfigNitrogenObjectiveMode"' in html
    assert "N-total instead of N forms" in html
    assert "nitrogen_objective_mode" in solver
    assert "n_total_only" in solver
    assert "n_forms_only" in solver
    assert 'id="solverConfigSObjectiveEnabled"' in html
    assert "s_objective_enabled" in constants


def test_solver_ui_merges_local_solver_config_fallbacks() -> None:
    solver = read_frontend_file("app/solver.js")
    assert "FALLBACK_SOLVER_CONFIG_DEFINITIONS.forEach" in solver
    assert "normalized.push({ ...definition })" in solver


def test_solver_advanced_config_lives_in_solver_panel() -> None:
    html = read_frontend_file("index.html")
    assert 'class="rail-advanced-config"' not in html
    assert 'class="solver-advanced-config"' in html
    assert html.index('id="solverMode"') < html.index('id="solverConfigResetDefaults"')
    assert html.index('class="solver-advanced-config"') < html.index('id="solverUreaToggle"')
    assert html.index('id="solverTargetsResultsTable"') < html.index('class="solver-advanced-config"')


def test_solver_config_reset_clears_persisted_overrides() -> None:
    solver = read_frontend_file("app/solver.js")
    reset = solver.split("solverConfigResetDefaultsButton?.addEventListener", 1)[1].split(
        "solverUreaToggle.addEventListener", 1
    )[0]
    assert "applySolverConfig();" in reset
    assert "renderSolverResults(null);" in reset
    assert "api.persistPreferences({ solver_config: {} });" in reset
    assert 'notifications.setSolverApplyStatus(t("solver.configResetDone"));' in reset


def test_recipe_solver_config_is_explicit_and_not_persisted_in_payloads() -> None:
    main = read_frontend_file("app/main.js")
    calculator = read_frontend_file("app/calculator.js")
    assert "if (recipe?.solver_config && Object.keys(recipe.solver_config).length)" in main
    assert "solver.applyConfig({ ...solver.buildConfigPayload(), ...recipe.solver_config });" in main
    recipe_payload = calculator.split("function buildRecipePayload(name", 1)[1].split(
        "function buildSolutionSnapshot", 1
    )[0]
    snapshot = calculator.split("function buildSolutionSnapshot()", 1)[1].split(
        "function initializeTables", 1
    )[0]
    assert "solver_config" not in recipe_payload
    assert "solver_config" not in snapshot
    assert "savedSolution.solver_config" not in main
