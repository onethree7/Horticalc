from pathlib import Path
import re


def test_solver_allowed_sync_button_present():
    index_html = Path(__file__).resolve().parents[1] / "frontend" / "index.html"
    content = index_html.read_text(encoding="utf-8")

    assert 'id="solverAllowedFromRecipe"' in content
    assert "Aus Rechner übernehmen" in content
    assert 'id="solverAllowedSearch"' in content
    assert 'id="solverAllowedSelectVisible"' in content
    assert 'id="solverAllowedDeselectVisible"' in content
    assert 'id="solverAllowedClear"' in content
    assert 'id="solverAllowedFertilizers" class="solver-picker"' in content
    assert not re.search(r'<select[^>]+id="solverAllowedFertilizers"', content)


def test_solver_allowed_sync_logic_present():
    app_js = Path(__file__).resolve().parents[1] / "frontend" / "app.js"
    content = app_js.read_text(encoding="utf-8")

    assert "syncSolverAllowedWithSelection" in content
    assert "solverAllowedFromRecipe" in content
    assert "getVisibleSolverAllowedOptions" in content
    assert "solverAllowedSearchInput" in content
    assert "rerenderPicker: false" in content


def test_solver_auto_apply_control_present():
    index_html = Path(__file__).resolve().parents[1] / "frontend" / "index.html"
    app_js = Path(__file__).resolve().parents[1] / "frontend" / "app.js"
    html_content = index_html.read_text(encoding="utf-8")
    js_content = app_js.read_text(encoding="utf-8")

    assert 'id="solverAutoApply" type="checkbox" checked' in html_content
    assert "Solver-Ergebnis automatisch im Rechner übernehmen" in html_content
    assert 'id="solverApplyStatus"' in html_content
    assert 'id="applySolverToCalculatorInline"' in html_content
    assert "SOLVER_AUTO_APPLY_KEY" in js_content
    assert "applySolverResultToCalculator" in js_content
    assert 'setSolverApplyStatus("Im Rechner übernommen")' in js_content
