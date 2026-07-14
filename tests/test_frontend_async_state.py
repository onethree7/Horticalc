from tests.frontend_assets import read_frontend_file


def test_calculation_and_solver_results_are_latest_request_only() -> None:
    calculator = read_frontend_file("app/calculator.js")
    solver = read_frontend_file("app/solver.js")
    assert "const calculationRequests = createLatestRequestGate();" in calculator
    assert "calculationRequests.reserve()" in calculator
    assert "calculationRequests.isCurrent(activeVersion)" in calculator
    assert "const solveRequests = createLatestRequestGate();" in solver
    assert "solveRequests.reserve()" in solver
    assert "solveRequests.isCurrent(version)" in solver


def test_profile_loads_are_latest_request_only() -> None:
    profiles = read_frontend_file("app/profiles.js")
    water = read_frontend_file("app/water.js")
    assert "const requests = createLatestRequestGate();" in profiles
    assert "requests.isCurrent(version)" in profiles
    assert "const waterProfileRequests = createLatestRequestGate();" in water
    assert "waterProfileRequests.isCurrent(version)" in water


def test_startup_resources_load_together_and_status_has_one_owner() -> None:
    main = read_frontend_file("app/main.js")
    notifications = read_frontend_file("app/notifications.js")
    startup = main.split("async function loadStartupResources()", 1)[1].split(
        "async function loadInitialWater", 1
    )[0]
    assert "Promise.allSettled([" in startup
    for loader in (
        "api.fetchSolverConfigDefinitions(",
        "api.fetchFertilizerCompKeys(",
        "api.fetchFertilizers(",
        "api.fetchMolarMasses(",
        "api.fetchWaterProfiles(",
        "api.fetchRecipes(",
        "api.fetchNutrientSolutions(",
        "api.fetchUnitDefinitions(",
    ):
        assert loader in startup
    assert "function finishStartup" in notifications
    assert "apiStatus.dataset.state" not in main
