from pathlib import Path


def test_solver_ui_hides_legacy_macro_and_stage_controls() -> None:
    index_html = Path(__file__).resolve().parents[1] / "frontend" / "index.html"
    content = index_html.read_text(encoding="utf-8")

    assert "Macro priority" not in content
    assert "Stage optimization" not in content
    assert 'id="solverConfigMacroPriorityEnabled"' not in content
    assert 'id="solverConfigStageOptimizationEnabled"' not in content


def test_solver_ui_fetches_backend_solver_config_schema() -> None:
    app_js = Path(__file__).resolve().parents[1] / "frontend" / "app.js"
    content = app_js.read_text(encoding="utf-8")

    assert "/schema/solver-config" in content
    assert "fetchSolverConfigDefinitions" in content
    assert "normalizeSolverConfigDefinitions" in content
