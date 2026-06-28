from tests.frontend_assets import read_frontend_file


def test_calculation_and_solver_results_are_latest_request_only() -> None:
    app_js = read_frontend_file("app.js")

    assert "const calculationRequests = createLatestRequestGate();" in app_js
    assert "calculationRequests.reserve()" in app_js
    assert "calculationRequests.isCurrent(activeVersion)" in app_js
    assert "const solveRequests = createLatestRequestGate();" in app_js
    assert "solveRequests.reserve()" in app_js
    assert "solveRequests.isCurrent(requestVersion)" in app_js


def test_profile_loads_are_latest_request_only() -> None:
    app_js = read_frontend_file("app.js")

    assert "const profileRequests = createLatestRequestGate();" in app_js
    assert "profileRequests.isCurrent(requestVersion)" in app_js
    assert "const waterProfileRequests = createLatestRequestGate();" in app_js
    assert "waterProfileRequests.isCurrent(requestVersion)" in app_js


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
