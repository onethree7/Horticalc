import re

from tests.frontend_assets import read_frontend_file


def test_solver_allowed_sync_button_present():
    content = read_frontend_file("index.html")

    assert 'id="solverAllowedFromRecipe"' in content
    assert 'data-i18n="solver.allowedFromRecipe"' in content
    assert 'id="solverAllowedSearch"' in content
    assert 'id="solverAllowedAll"' in content
    assert 'data-i18n="common.all"' in content
    assert 'id="solverAllowedHideInactive"' in content
    assert 'data-i18n="solver.onlyActive"' in content
    assert 'id="solverAllowedSelectVisible"' not in content
    assert 'id="solverAllowedDeselectVisible"' not in content
    assert "Sichtbare auswählen" not in content
    assert "Sichtbare abwählen" not in content
    assert 'id="solverAllowedClear"' in content
    assert 'id="solverAllowedFertilizers" class="table-wrap solver-picker"' in content
    assert 'id="solverOverrides" class="solver-overrides"' in content
    assert 'data-i18n="solver.overrideTitle"' in content
    assert not re.search(r'<select[^>]+id="solverAllowedFertilizers"', content)

def test_solver_allowed_sync_logic_present():
    content = read_frontend_file("app/solver.js")

    assert "syncSolverAllowedWithSelection" in content
    assert "solverAllowedFromRecipe" in content
    assert "getVisibleSolverAllowedOptions" in content
    assert "solverAllowedSearchInput" in content
    assert "solverAllowedAllButton" in content
    assert "solverAllowedHideInactiveInput" in content
    assert "solverAllowedHideInactive" in content
    assert "fertilizerOptions.map(({ name }) => name)" in content
    assert "rerenderPicker: false" in content
    assert 'table.className = "grid grid--form solver-picker-table"' in content
    assert "document.createElement(\"tr\")" in content
    assert "document.createElement(\"td\")" in content

def test_solver_auto_apply_control_present():
    html_content = read_frontend_file("index.html")
    solver = read_frontend_file("app/solver.js")
    calculator = read_frontend_file("app/calculator.js")

    assert 'id="solverAutoApply" type="checkbox" checked' in html_content
    assert 'data-i18n="solver.autoApply"' in html_content
    assert 'id="solverApplyStatus"' in html_content
    assert 'id="applySolverToCalculatorInline"' in html_content
    assert html_content.index('id="solveBtn"') < html_content.index('id="solverAutoApply"')
    assert "SOLVER_AUTO_APPLY_KEY" in solver
    assert "applySolverResultToCalculator" in calculator
    assert 'setSolverApplyStatus(t("status.appliedCalculator"))' in calculator

def test_solver_override_panel_is_optional_and_auto_opens_when_active():
    content = read_frontend_file("app/solver.js")

    assert "solverOverridesDetails" in content
    assert "solverOverrideSummary" in content
    assert "function syncSolverOverridePanel" in content
    assert "solverOverridesDetails.open = true" in content
    assert "forceOpen: solverFixedGrams[name] > 0" in content
