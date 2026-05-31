from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]


def _read_frontend_file(name: str) -> str:
    return (ROOT / "frontend" / name).read_text(encoding="utf-8")


def test_horticalc_shell_replaces_visible_mode_menu() -> None:
    content = _read_frontend_file("index.html")

    assert 'id="modeSection"' not in content
    assert 'aria-label="Modus-Auswahl"' not in content
    assert 'class="page-header app-header"' not in content
    assert 'data-testid="horticalc-app-frame"' in content
    assert 'data-testid="horticalc-rail"' in content
    assert 'data-testid="rail-brand"' in content
    assert 'id="modeStateControls"' in content
    assert "recipe-wheel" not in content
    assert "wheel-" not in content


def test_workflow_steps_and_editor_utility_exist_in_order() -> None:
    content = _read_frontend_file("index.html")
    expected_steps = [
        'data-shell-view="editor"',
        'data-shell-view="water"',
        'data-shell-view="fertilizers"',
        'data-shell-view="solver"',
    ]

    positions = [content.index(step) for step in expected_steps]
    assert positions == sorted(positions)
    assert 'data-testid="workflow-guide"' in content
    assert 'data-testid="workflow-nav"' in content
    assert 'workflow-step--solver' in content
    assert 'workflow-step--manual' not in content
    assert 'data-testid="workflow-calculate"' not in content
    assert 'data-testid="workflow-results"' not in content
    assert 'data-testid="workflow-details"' not in content
    assert 'data-shell-view="calculate"' not in content
    assert 'data-shell-view="results"' not in content
    assert 'data-shell-view="details"' not in content
    assert "<span>DÜNGER-EDITOR</span>" in content
    assert "<span>WASSERWERTE</span>" in content
    assert "<span>RECHNER</span>" in content
    assert "<span>SOLVER</span>" in content
    assert "Erstelle oder lade eigene Dünger im <span>DÜNGER-EDITOR</span>." in content
    assert "Konfiguriere deine <span>WASSERWERTE</span>." in content
    assert "Erstelle Rezepte von Hand im <span>RECHNER</span>." in content
    assert "Oder lass den <span>SOLVER</span> für dich lösen." in content
    assert 'class="workflow-step-index"' not in content
    assert "<span>0</span>" not in content
    assert "<span>1</span>" not in content
    assert "<span>2a</span>" not in content
    assert "<span>2b</span>" not in content
    assert 'data-testid="rail-api-controls"' in content
    assert 'data-testid="rail-config-controls"' in content
    assert 'id="configLiters"' in content
    assert 'id="configLitersStatus"' in content
    assert 'id="osmosisPercent"' in content
    assert 'id="waterUnitToggle"' in content
    assert "Solver Advanced Config" in content
    assert 'id="solverConfigResetDefaults"' in content
    assert 'id="solverConfigRelativeWeighting"' in content
    assert 'id="solverConfigNTotalGovernorEnabled"' in content
    assert 'id="solverLiters"' not in content
    assert 'id="applyScaleToCalcLiters"' not in content
    assert "API Base URL" not in content
    assert "Daten laden" not in content
    assert 'data-testid="active-view-status"' not in content
    assert 'id="activeShellLabel"' not in content
    assert 'data-testid="live-bar"' in content
    assert 'id="npkAllPct"' in content
    assert 'id="npkPNorm"' in content
    assert 'id="npkNpkPct"' in content
    assert 'id="ec25Value"' in content
    assert 'id="ec18Value"' in content
    assert 'id="ecWater25Value"' in content
    assert 'id="ecWater18Value"' in content
    assert content.count('id="npkAllPct"') == 1
    assert content.count('id="ecWater18Value"') == 1
    assert "Wasser</span>" in content
    assert "live-metric--npk" in content
    assert "live-metric--ratio" in content
    assert "Hydroponic Solution Calculator and powerful Nutrient Solver." in content
    assert "Nährlösung-Rechner" not in content
    assert "live-metric" in content
    assert "summary-metrics" not in content
    assert content.index('data-testid="rail-brand"') < content.index('data-testid="rail-api-controls"')
    assert content.index('data-testid="rail-api-controls"') < content.index('data-testid="rail-config-controls"')
    assert content.index('data-testid="rail-config-controls"') < content.index('data-testid="workflow-guide"')
    assert content.index('data-testid="workflow-guide"') < content.index('data-testid="workflow-nav"')
    assert content.index('data-testid="live-bar"') < content.index('data-testid="workspace-scroll-frame"')


def test_critical_frontend_ids_remain_available() -> None:
    content = _read_frontend_file("index.html")
    required_ids = [
        "calculatorMode",
        "solverMode",
        "fertilizerEditorMode",
        "waterSection",
        "profileSection",
        "fertilizerSelectTableWrap",
        "calculatorTableWrap",
        "waterValuesTable",
        "summaryViewToggle",
        "waterSummaryTable",
        "oxideSummaryTable",
        "ionSummaryTable",
        "ionMeqList",
        "ionBalanceList",
        "solverTargetsTable",
        "solverAllowedFertilizers",
        "solverFixedTable",
        "solveBtn",
        "copySolverResults",
        "applySolverToCalculator",
        "saveSolverAsRecipe",
    ]

    for element_id in required_ids:
        assert f'id="{element_id}"' in content


def test_frontend_has_no_duplicate_ids() -> None:
    content = _read_frontend_file("index.html")
    ids = re.findall(r'id="([^"]+)"', content)
    duplicates = sorted({element_id for element_id in ids if ids.count(element_id) > 1})

    assert duplicates == []


def test_app_js_shell_helpers_are_top_level_and_initialized() -> None:
    content = _read_frontend_file("app.js")

    for helper in [
        "function bindShellNavigation()",
        "function setActiveShellView(view)",
        "function showShellView(view",
        "function scrollToPanelAnchor(anchor",
        "function updateLiveResultBar(data = lastCalculation)",
    ]:
        assert helper in content

    assert "bindShellNavigation();" in content
    assert "function buildSolverConfigPayload()" in content
    assert "let currentLiters = DEFAULT_LITERS;" in content
    assert "CALC_LITERS" not in content
    assert "solverLitersInput" not in content
    assert "applyScaleToCalcLiters" not in content
    assert 'showShellView("fertilizers", { scroll: false });' in content
    assert "renderCalculation(data)" in content
    assert "updateLiveResultBar(data);" in content
    assert 'label: "RECHNER"' in content
    assert 'label: "SOLVER"' in content


def test_framed_shell_styles_present() -> None:
    content = _read_frontend_file("styles.css")

    assert ".app-shell" in content
    assert ".app-rail" in content
    assert ".workflow-nav" in content
    assert ".workflow-step" in content
    assert "overflow: visible" in content
    assert "line-height: 1.25" in content
    assert ".rail-guide-list" in content
    assert "--app-solver" in content
    assert ".workflow-step.is-active" in content
    assert ".workspace" in content
    assert "overflow-y: auto" in content
    assert ".live-bar" in content
    assert ".rail-config" in content
    assert ".btn--solver-primary" in content
    assert ".live-metric--npk" in content
    assert ".live-metric--ratio" in content
    assert ".live-ec" in content
    assert "scrollbar-gutter: stable" in content
    assert "--app-min-width" not in content
    assert "min-width: calc(var(--app-min-width)" not in content
    assert "overflow-x: hidden" in content
    assert "width: 100%" in content
    assert ".summary-metric-card:first-child" not in content
    assert ".mode-toggle" not in content
    assert ".brand-kicker" not in content
    assert ".gap-3" not in content
    assert "@media (max-width: 980px)" in content
    assert ".recipe-wheel" not in content
    assert ".wheel-" not in content


def test_fertilizer_editor_sticky_columns_size_from_visible_content() -> None:
    styles = _read_frontend_file("styles.css")
    app_js = _read_frontend_file("app.js")

    assert "--fert-editor-index-width" in styles
    assert "--fert-editor-form-width" in styles
    assert "--fert-editor-weight-width" in styles
    assert "left: var(--fert-editor-index-width)" in styles
    assert "left: calc(var(--fert-editor-index-width) + 18rem)" in styles
    assert "left: calc(var(--fert-editor-index-width) + 18rem + var(--fert-editor-form-width))" in styles
    assert "const indexDigitCount = String(Math.max(1, filteredRows.length)).length;" in app_js
    assert "const formWidthCh = contentWidthCh(filteredRows.map(({ row }) => row.form), \"Form\", 4);" in app_js
    assert "const weightWidthCh = contentWidthCh(" in app_js
    assert "calc(${indexDigitCount}ch + (var(--space-2) * 2))" in app_js
    assert "calc(${formWidthCh + 1}ch + (var(--space-2) * 2))" in app_js
    assert "calc(${weightWidthCh + 1}ch + (var(--space-2) * 2))" in app_js


def test_fertilizer_editor_sticky_columns_paint_opaque_backgrounds() -> None:
    styles = _read_frontend_file("styles.css")

    assert "#fertilizerEditorTable th {\n  background: #202c30;" in styles
    assert "#fertilizerEditorTable input {\n  border-color: rgba(174, 183, 166, 0.16);\n  background: #0a100f;" in styles
    assert "#fertilizerEditorTable tbody tr:nth-child(odd) td:nth-child(-n + 4) {\n  background: #141b14;" in styles
    assert "#fertilizerEditorTable tbody tr:nth-child(even) td:nth-child(-n + 4) {\n  background: #0e1410;" in styles


def test_live_result_bar_uses_consistent_high_visibility_type() -> None:
    styles = _read_frontend_file("styles.css")
    index = _read_frontend_file("index.html")

    assert "--live-value-size: 1.18rem" in styles
    assert ".live-metric strong" in styles
    assert ".live-ec .ec-value" in styles
    assert "font-size: var(--live-value-size)" in styles
    assert ".live-ec .metric-title {\n  margin-bottom: var(--space-2);" in styles
    assert "text-transform: none" in styles
    assert "letter-spacing: 0" in styles
    assert "EC (mS/cm)" in index
