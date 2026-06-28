from tests.frontend_assets import read_frontend_file


def test_calculation_and_solver_results_are_latest_request_only() -> None:
    app_js = read_frontend_file("app.js")

    assert "let calculationRequestVersion = 0;" in app_js
    assert "const requestVersion = ++calculationRequestVersion;" in app_js
    assert "activeVersion !== calculationRequestVersion" in app_js
    assert "let solveRequestVersion = 0;" in app_js
    assert "const requestVersion = ++solveRequestVersion;" in app_js
    assert "requestVersion !== solveRequestVersion" in app_js


def test_profile_loads_are_latest_request_only() -> None:
    app_js = read_frontend_file("app.js")

    assert "let profileRequestVersion = 0;" in app_js
    assert "requestVersion !== profileRequestVersion" in app_js
    assert "let waterProfileRequestVersion = 0;" in app_js
    assert "requestVersion !== waterProfileRequestVersion" in app_js


def test_startup_resources_load_together_and_own_system_status() -> None:
    app_js = read_frontend_file("app.js")
    startup_block = app_js.split("async function loadStartupResources()", 1)[1].split(
        "function finishStartupStatus", 1
    )[0]
    report_error_block = app_js.split("function reportError", 1)[1].split(
        "function getMolarMass", 1
    )[0]

    assert "Promise.allSettled([" in startup_block
    for loader in (
        "fetchSolverConfigDefinitions()",
        "fetchFertilizerCompKeys()",
        "fetchFertilizers()",
        "fetchMolarMasses()",
        "fetchWaterProfiles()",
        "fetchRecipes()",
        "fetchNutrientSolutions()",
    ):
        assert loader in startup_block
    assert "setApiStatus" not in report_error_block
    assert 'setApiStatus(t("status.dataIncomplete"), "error")' in app_js
