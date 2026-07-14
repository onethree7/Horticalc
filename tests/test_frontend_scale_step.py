from tests.frontend_assets import read_frontend_file


def test_scale_step_buttons_use_fixed_increment():
    scaling = read_frontend_file("app/scaling.js")
    calculator = read_frontend_file("app/calculator.js")
    solver = read_frontend_file("app/solver.js")

    assert "function bindScaleButtons" in scaling
    assert "step = 0.05" in scaling
    assert "applyFactor(currentFactor() - step)" in scaling
    assert "applyFactor(currentFactor() + step)" in scaling
    assert "applySolverTargetScaleFactor" in solver
    assert "applyCalculatorScaleFactor" in calculator


def test_calculator_rows_use_one_state_model():
    content = read_frontend_file("app/calculator.js")

    assert "let calculatorRows = [createCalculatorRow()];" in content
    assert "function createCalculatorRow(" in content
    assert "selectedFertilizers" not in content
    assert "fertilizerAmounts" not in content
    assert "calculatorBaseAmounts" not in content
