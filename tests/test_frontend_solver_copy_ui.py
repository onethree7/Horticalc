from pathlib import Path


def test_solver_copy_button_present() -> None:
    index_html = Path(__file__).resolve().parents[1] / "frontend" / "index.html"
    content = index_html.read_text(encoding="utf-8")

    assert 'id="copySolverResults"' in content
    assert "In Zwischenablage kopieren" in content
    assert 'id="copySolverResultsStatus"' in content


def test_solver_copy_logic_present() -> None:
    app_js = Path(__file__).resolve().parents[1] / "frontend" / "app.js"
    content = app_js.read_text(encoding="utf-8")

    assert "buildSolverClipboardText" in content
    assert "buildClipboardRows" in content
    assert "copySolverResultsToClipboard" in content
    assert "copyTextWithFallback" in content
    assert "Ansatz (L)" in content
    assert "Solver Zielwerte (mg/L)" in content
    assert "EC (mS/cm)" in content
    assert "\\t" not in content
    assert '.join("  ")' in content
