from pathlib import Path
import re


def test_solver_allowed_sync_button_present():
    index_html = Path(__file__).resolve().parents[1] / "frontend" / "index.html"
    content = index_html.read_text(encoding="utf-8")

    assert 'id="solverAllowedFromRecipe"' in content
    assert "Aus Rechner übernehmen" in content
    assert 'id="solverAllowedSearch"' in content
    assert 'id="solverAllowedAll"' in content
    assert "Alle" in content
    assert 'id="solverAllowedHideInactive"' in content
    assert "Nur aktive" in content
    assert 'id="solverAllowedSelectVisible"' not in content
    assert 'id="solverAllowedDeselectVisible"' not in content
    assert "Sichtbare auswählen" not in content
    assert "Sichtbare abwählen" not in content
    assert 'id="solverAllowedClear"' in content
    assert 'id="solverAllowedFertilizers" class="table-wrap solver-picker"' in content
    assert 'id="solverOverrides" class="solver-overrides"' in content
    assert "Override / fixe Menge (g, optional)" in content
    assert not re.search(r'<select[^>]+id="solverAllowedFertilizers"', content)


def test_solver_allowed_sync_logic_present():
    app_js = Path(__file__).resolve().parents[1] / "frontend" / "app.js"
    content = app_js.read_text(encoding="utf-8")

    assert "syncSolverAllowedWithSelection" in content
    assert "solverAllowedFromRecipe" in content
    assert "getVisibleSolverAllowedOptions" in content
    assert "solverAllowedSearchInput" in content
    assert "solverAllowedAllButton" in content
    assert "solverAllowedHideInactiveInput" in content
    assert "solverAllowedHideInactive" in content
    assert "fertilizerOptions.map((fert) => fert.name)" in content
    assert "rerenderPicker: false" in content
    assert 'table.className = "grid grid--form solver-picker-table"' in content
    assert "document.createElement(\"tr\")" in content
    assert "document.createElement(\"td\")" in content


def test_solver_auto_apply_control_present():
    index_html = Path(__file__).resolve().parents[1] / "frontend" / "index.html"
    app_js = Path(__file__).resolve().parents[1] / "frontend" / "app.js"
    html_content = index_html.read_text(encoding="utf-8")
    js_content = app_js.read_text(encoding="utf-8")

    assert 'id="solverAutoApply" type="checkbox" checked' in html_content
    assert "Auto übernehmen" in html_content
    assert 'id="solverApplyStatus"' in html_content
    assert 'id="applySolverToCalculatorInline"' in html_content
    assert html_content.index('id="solveBtn"') < html_content.index('id="solverAutoApply"')
    assert html_content.index('id="solverAutoApply"') < html_content.index('id="copySolverResults"')
    assert "SOLVER_AUTO_APPLY_KEY" in js_content
    assert "applySolverResultToCalculator" in js_content
    assert 'setSolverApplyStatus("Im Rechner übernommen")' in js_content


def test_solver_override_panel_is_optional_and_auto_opens_when_active():
    app_js = Path(__file__).resolve().parents[1] / "frontend" / "app.js"
    content = app_js.read_text(encoding="utf-8")

    assert "solverOverridesDetails" in content
    assert "solverOverrideSummary" in content
    assert "function syncSolverOverridePanel" in content
    assert "solverOverridesDetails.open = true" in content
    assert "forceOpen: Number(event.target.value) > 0" in content
