from pathlib import Path


def test_solver_allowed_sync_button_present():
    index_html = Path(__file__).resolve().parents[1] / "frontend" / "index.html"
    content = index_html.read_text(encoding="utf-8")

    assert 'id="solverAllowedFromRecipe"' in content
    assert "Allowed aus Rezept übernehmen" in content


def test_solver_allowed_sync_logic_present():
    app_js = Path(__file__).resolve().parents[1] / "frontend" / "app.js"
    content = app_js.read_text(encoding="utf-8")

    assert "syncSolverAllowedWithSelection" in content
    assert "solverAllowedFromRecipe" in content
