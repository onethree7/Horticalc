from tests.frontend_assets import read_frontend_file


def test_scale_step_buttons_use_fixed_increment():
    content = read_frontend_file("app.js")

    assert "const SCALE_STEP = 0.05;" in content
    assert "function bindScaleButtons" in content
    assert "applyFactor(currentFactor() - SCALE_STEP);" in content
    assert "applyFactor(currentFactor() + SCALE_STEP);" in content
    assert "applySolverTargetScaleFactor" in content
    assert "applyCalculatorScaleFactor" in content
