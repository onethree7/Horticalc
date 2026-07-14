from tests.frontend_assets import read_frontend_file


def test_heavy_workflow_tables_are_owned_by_feature_lifecycle() -> None:
    main = read_frontend_file("app/main.js")
    editor = read_frontend_file("app/editor.js")
    solver = read_frontend_file("app/solver.js")
    assert 'if (previousView === "editor") editor.deactivate();' in main
    assert 'if (previousView === "solver") solver.deactivate();' in main
    assert "fertilizerEditorTableWrap.replaceChildren();" in editor
    assert "solverAllowedFertilizersSelect.replaceChildren();" in solver
    assert "applyFertilizerEditorFilter();" in editor
    assert "row.hidden = !visible;" in editor
    assert "window.setTimeout(renderSolverAllowedOptions, 150)" in solver


def test_locale_refresh_calls_only_explicit_controller_contracts() -> None:
    main = read_frontend_file("app/main.js")
    refresh = main.split("function refreshLocalizedUi()", 1)[1].split(
        "settings = createSettingsController", 1
    )[0]
    assert "applyDomTranslations" not in refresh
    assert "settings.render();" in refresh
    assert "profiles.refreshLocalized();" in refresh
    assert "calculator.refreshLocalized();" in refresh
    assert "solver.refreshLocalized();" in refresh
    assert "editor.refreshLocalized();" in refresh


def test_catalog_refresh_flows_through_composition_root() -> None:
    editor = read_frontend_file("app/editor.js")
    main = read_frontend_file("app/main.js")
    refresh = editor.split("async function refreshFertilizerCatalog()", 1)[1].split(
        "async function saveFertilizerEditor()", 1
    )[0]
    assert "onCatalogChange(refreshedFertilizers);" in refresh
    assert "calculator.setFertilizers(fertilizers);" in main
    assert "solver.setFertilizers(fertilizers);" in main


def test_preferences_and_startup_resources_begin_concurrently() -> None:
    main = read_frontend_file("app/main.js")
    init = main.split("async function init()", 1)[1]
    assert "Promise.all([api.loadPreferences(), loadStartupResources()])" in init
