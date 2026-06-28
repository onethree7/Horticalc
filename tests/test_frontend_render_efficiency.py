from tests.frontend_assets import read_frontend_file


def test_heavy_workflow_tables_are_lazy_and_editor_search_reuses_rows() -> None:
    app = read_frontend_file("app.js")

    assert "const FERTILIZER_EDITOR_SEARCH_DELAY_MS = 150;" in app
    assert 'currentShellView !== "editor"' in app
    assert 'currentShellView !== "solver"' in app
    assert "function releaseInactiveHeavyViews()" in app
    assert "fertilizerEditorTableWrap.replaceChildren();" in app
    assert "solverAllowedFertilizersSelect.replaceChildren();" in app
    assert "function applyFertilizerEditorFilter()" in app
    assert "row.hidden = !visible;" in app
    assert "applyFertilizerEditorFilter();" in app
    assert "renderFertilizerEditorPager" not in app


def test_language_refresh_does_not_repeat_dom_translation() -> None:
    app = read_frontend_file("app.js")
    refresh_block = app.split("function refreshLocalizedUi()", 1)[1].split(
        "function buildRecipePayload(",
        1,
    )[0]

    assert "applyDomTranslations" not in refresh_block
    assert 'currentShellView === "editor"' in refresh_block
    assert 'currentShellView === "solver"' in refresh_block
    assert 'currentShellView === "water"' in refresh_block


def test_catalog_refresh_resets_solver_results_once_through_owner() -> None:
    app = read_frontend_file("app.js")
    refresh_block = app.split("async function refreshFertilizerCatalog()", 1)[1].split(
        "async function saveFertilizerEditor()",
        1,
    )[0]
    update_block = app.split("function updateSolverAllowedFertilizers", 1)[1].split(
        "function normalizeSolverAllowedContext",
        1,
    )[0]

    assert 'updateSolverAllowedFertilizers(availableSolverNames, "replace")' in refresh_block
    assert "renderSolverResults(null);" not in refresh_block
    assert update_block.count("renderSolverResults(null);") == 1


def test_preferences_and_startup_resources_begin_concurrently() -> None:
    app = read_frontend_file("app.js")
    init_block = app.split("async function init()", 1)[1].split(
        "addRowButton.addEventListener",
        1,
    )[0]

    assert "const [preferences, startupResources] = await Promise.all([" in init_block
    assert "loadPreferences()," in init_block
    assert "loadStartupResources()," in init_block
