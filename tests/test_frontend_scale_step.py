from pathlib import Path


def test_scale_step_buttons_use_fixed_increment():
    app_js = Path(__file__).resolve().parents[1] / "frontend" / "app.js"
    content = app_js.read_text(encoding="utf-8")

    assert "const SCALE_STEP = 0.1;" in content
    assert "applySolverTargetScaleFactor(solverTargetScaleFactor - SCALE_STEP);" in content
    assert "applySolverTargetScaleFactor(solverTargetScaleFactor + SCALE_STEP);" in content
    assert "applyCalculatorScaleFactor(calculatorScaleFactor - SCALE_STEP);" in content
    assert "applyCalculatorScaleFactor(calculatorScaleFactor + SCALE_STEP);" in content
