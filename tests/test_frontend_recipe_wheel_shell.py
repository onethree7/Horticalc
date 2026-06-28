import re

from tests.frontend_assets import read_frontend_file

def test_horticalc_shell_replaces_visible_mode_menu() -> None:
    content = read_frontend_file("index.html")

    assert 'id="modeSection"' not in content
    assert 'aria-label="Modus-Auswahl"' not in content
    assert 'class="page-header app-header"' not in content
    assert 'data-testid="horticalc-app-frame"' in content
    assert 'data-testid="horticalc-rail"' in content
    assert 'data-testid="rail-brand"' in content
    assert 'id="modeStateControls"' not in content
    assert 'name="modeToggle"' not in content
    assert "recipe-wheel" not in content
    assert "wheel-" not in content

def test_workflow_steps_and_editor_utility_exist_in_order() -> None:
    content = read_frontend_file("index.html")
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
    assert 'data-i18n="workflow.editor"' in content
    assert 'data-i18n="workflow.water"' in content
    assert 'data-i18n="workflow.calculator"' in content
    assert 'data-i18n="workflow.solver"' in content
    assert 'data-i18n="workflow.menu"' in content
    assert 'data-i18n="workflow.shortGuide"' in content
    assert 'data-i18n="workflow.guide.editor"' in content
    assert 'data-i18n="workflow.guide.water"' in content
    assert 'data-i18n="workflow.guide.calculator"' in content
    assert 'data-i18n="workflow.guide.solver"' in content
    assert 'class="workflow-step-index"' in content
    assert 'class="workflow-step-hint"' in content
    assert "<span>0</span>" not in content
    assert "<span>1</span>" not in content
    assert "<span>2a</span>" not in content
    assert "<span>2b</span>" not in content
    assert 'data-testid="rail-api-controls"' in content
    assert 'data-testid="rail-config-controls"' in content
    assert 'id="configLiters"' in content
    assert 'id="configLitersStatus"' in content
    assert 'id="themeSelect"' in content
    assert 'id="languageSelect"' in content
    assert "Horticalc Dark" in content
    assert "Soil" in content
    rail_config_block = content.split('data-testid="rail-config-controls"', 1)[1].split("</section>", 1)[0]
    assert 'data-i18n-aria-label="aria.theme"' in rail_config_block
    assert 'data-i18n-aria-label="aria.language"' in rail_config_block
    assert 'id="osmosisPercent"' in content
    assert 'id="waterUnitToggle"' in content
    assert "Solver Advanced Config" not in content
    assert 'class="solver-advanced-config"' in content
    assert 'data-i18n="solver.advanced"' in content
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
    assert 'id="caMgRatio"' in content
    assert 'id="ionRatioList"' in content
    assert 'id="ec25Value"' in content
    assert 'id="ec18Value"' in content
    assert 'id="ecWater25Value"' in content
    assert 'id="ecWater18Value"' in content
    assert content.count('id="npkAllPct"') == 1
    assert content.count('id="ecWater18Value"') == 1
    assert 'data-i18n="live.water"' in content
    assert "live-metric--npk" in content
    assert "live-metric--ratio" in content
    assert "live-metric--camg" in content
    assert "live-ion-ratios" in content
    assert "Hydroponic Solution Calculator and powerful Nutrient Solver." in content
    assert "Nährlösung-Rechner" not in content
    assert "live-metric" in content
    assert "summary-metrics" not in content
    assert content.index('data-testid="rail-brand"') < content.index('data-testid="rail-api-controls"')
    assert content.index('data-testid="rail-api-controls"') < content.index('data-testid="rail-config-controls"')
    assert content.index('data-testid="rail-config-controls"') < content.index('data-testid="workflow-nav"')
    assert content.index('data-testid="workflow-nav"') < content.index('data-testid="workflow-guide"')
    assert content.index('data-testid="live-bar"') < content.index('data-testid="workspace-scroll-frame"')

def test_critical_frontend_ids_remain_available() -> None:
    content = read_frontend_file("index.html")
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
    content = read_frontend_file("index.html")
    ids = re.findall(r'id="([^"]+)"', content)
    duplicates = sorted({element_id for element_id in ids if ids.count(element_id) > 1})

    assert duplicates == []

def test_theme_adaptive_icon_sprite_is_reused_by_workflow_and_headings() -> None:
    content = read_frontend_file("index.html")
    styles = read_frontend_file("styles.css")
    symbol_ids = [
        "icon-editor",
        "icon-water",
        "icon-recipe",
        "icon-components",
        "icon-calculator",
        "icon-solver",
        "icon-balance",
    ]

    for symbol_id in symbol_ids:
        assert content.count(f'id="{symbol_id}"') == 1
        assert f'href="#{symbol_id}"' in content

    assert content.count('class="workflow-step-number"') == 4
    assert content.count('class="heading-icon"') == 7
    assert '<h2 data-i18n="water.title">Water values</h2>' in content
    assert '<h2 data-i18n="calculator.title">Hydroponic Solution Calculator</h2>' in content
    assert '<h2 data-i18n="solver.title">Target profile calculator</h2>' in content
    assert '.app-icon .icon-accent' in styles
    assert 'stroke: var(--app-teal);' in styles
    assert 'width: 1.82rem;' in styles
    assert 'width: 2.02rem;' in styles
    assert 'class="icon-fertilizer-bags"' in content
    assert "NPK</text>" not in content
    assert 'class="icon-tap"' in content
    assert 'class="icon-calculator-body"' in content
    assert 'class="icon-accent icon-target-leaf"' in content
    assert 'class="icon-molecule-bonds"' in content
    assert content.count('icon-molecule-atom') == 5
    assert "NaCl" not in content
    assert '.workspace .block > h2:first-child::before' not in styles

def test_brand_window_uses_single_clean_leaf() -> None:
    content = read_frontend_file("index.html")
    styles = read_frontend_file("styles.css")

    assert 'class="brand-leaf-shape"' in content
    assert 'class="brand-leaf-vein"' in content
    assert '.rail-logo .brand-leaf-shape' in styles
    assert '.rail-logo .brand-leaf-vein' in styles

def test_app_js_shell_helpers_are_top_level_and_initialized() -> None:
    content = read_frontend_file("app.js")

    for helper in [
        "function bindShellNavigation()",
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
    assert "applySolverResultToCalculator" in content
    assert "solverAutoApplyEnabled" in content
    assert "modeToggleInputs" not in content
    assert "activeShellView" not in content
    assert "activeMode" not in content

def test_framed_shell_styles_present() -> None:
    content = read_frontend_file("styles.css")

    assert ".app-shell" in content
    assert ".app-rail" in content
    assert ".workflow-nav" in content
    assert ".workflow-step" in content
    assert "overflow: visible" in content
    assert "line-height: 1.25" in content
    assert ".rail-guide-list" in content
    assert "--app-solver" in content
    assert ".workflow-step.is-active" in content
    assert ".solver-workbench" in content
    assert ".solver-picker" in content
    assert ".solver-comparison-grid" in content
    assert ".workspace" in content
    assert "overflow-y: auto" in content
    assert ".live-bar" in content
    assert ".rail-config" in content
    assert ".btn--solver-primary" in content
    assert ".live-metric--npk" in content
    assert ".live-metric--ratio" in content
    assert ".live-metric--camg" in content
    assert ".live-ec" in content
    assert ".live-ion-ratios" in content
    assert ".rail-theme-control" in content
    assert '.app-body[data-theme="horticalc-light"]' in content
    assert '.app-body[data-theme="high-contrast"]' in content
    assert '.app-body[data-theme="soil"]' in content
    assert '.app-body[data-theme="vt-green"]' in content
    assert '.app-body[data-theme="blue-matrix"]' in content
    assert "--app-table-row-odd" in content
    assert "--app-live-primary" in content
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
    intermediate_styles = content.split("@media (max-width: 980px)", 1)[1].split(
        "@media (max-width: 640px)", 1
    )[0]
    intermediate_rail = intermediate_styles.split(".app-rail {", 1)[1].split("}", 1)[0]
    assert "align-items: start;" not in intermediate_rail
    assert ".rail-workflow,\n  .live-bar {\n    grid-column: 1 / -1;" in content
    assert ".live-bar {\n    grid-template-columns: repeat(2, minmax(0, 1fr));" in content
    assert ".live-ion-ratios .ion-ratio-grid {\n    grid-template-columns: repeat(3, minmax(0, 1fr));" in content
    assert "@media (max-width: 640px)" in content
    assert ".live-bar {\n    grid-template-columns: 1fr;" in content
    assert ".recipe-wheel" not in content
    assert ".wheel-" not in content

def test_theme_selector_persists_browser_design_state() -> None:
    app_js = read_frontend_file("app.js")

    assert 'const THEME_STORAGE_KEY = "horticalc.theme";' in app_js
    assert 'const DEFAULT_THEME = "horticalc-dark";' in app_js
    assert 'document.body.dataset.theme = nextTheme;' in app_js
    assert "async function initializeThemeControl()" in app_js
    assert "lsGet(THEME_STORAGE_KEY, DEFAULT_THEME)" in app_js
    assert 'fetch(`${apiBase()}/preferences`' in app_js
    assert "persistPreferences({ theme: nextTheme });" in app_js
    assert "body: JSON.stringify(updates)" in app_js
    assert "keepalive: true" in app_js


def test_workspace_preferences_persist_without_overwriting_explicit_recipe_loads() -> None:
    app_js = read_frontend_file("app.js")

    assert "persistPreferences({ default_liters: nextLiters });" in app_js
    assert "persistPreferences({ solver_config: buildSolverConfigPayload() });" in app_js
    assert "persistPreferences({ last_water_profile: selection });" in app_js
    assert 'persistPreferences({ last_water_profile: "default.yml" });' in app_js
    assert "let preferenceWritePromise = Promise.resolve();" in app_js
    assert "preferenceWritePromise = preferenceWritePromise.then(() =>" in app_js
    assert "return preferenceWritePromise;" in app_js
    assert "applyRecipe(recipe, { applyLiters: false });" in app_js
    assert "applyRecipe(recipe);" in app_js

def test_fertilizer_editor_sticky_columns_size_from_visible_content() -> None:
    styles = read_frontend_file("styles.css")
    app_js = read_frontend_file("app.js")

    assert "--fert-editor-index-width" in styles
    assert "--fert-editor-liquid-width" in styles
    assert "--fert-editor-weight-width" in styles
    assert "left: var(--fert-editor-index-width)" in styles
    assert "--fert-editor-name-width: 18rem" in styles
    assert "--fert-editor-liquid-width: 58px" in styles
    assert "--fert-editor-weight-width: 52px" in styles
    assert "left: calc(var(--fert-editor-index-width) + var(--fert-editor-name-width))" in styles
    assert "left: calc(var(--fert-editor-index-width) + var(--fert-editor-name-width) + var(--fert-editor-liquid-width))" in styles
    assert "const indexDigitCount = String(Math.max(1, sortedRows.length)).length;" in app_js
    assert "calc(${indexDigitCount}ch + (var(--space-2) * 2))" in app_js
    assert "addFertilizerNameColumnResizer" in app_js
    assert 'table.style.setProperty("--fert-editor-name-width"' in app_js
    assert "Math.min(640, Math.max(180" in app_js
    assert '#fertilizerEditorTable th:nth-child(3) .table-sort-button' in styles

def test_fertilizer_editor_sticky_columns_paint_opaque_backgrounds() -> None:
    styles = read_frontend_file("styles.css")

    assert "#fertilizerEditorTable th {\n  background: var(--app-fert-editor-head-bg);" in styles
    assert (
        "#fertilizerEditorTable input {\n"
        "  border-color: rgba(174, 183, 166, 0.16);\n"
        "  background: var(--app-fert-editor-input-bg);"
    ) in styles
    assert (
        "#fertilizerEditorTable tbody tr:nth-child(odd) td:nth-child(-n + 4) {\n"
        "  background: var(--app-fert-editor-row-odd-bg);"
    ) in styles
    assert (
        "#fertilizerEditorTable tbody tr:nth-child(even) td:nth-child(-n + 4) {\n"
        "  background: var(--app-fert-editor-row-even-bg);"
    ) in styles
    assert styles.count("--app-fert-editor-row-odd-bg:") == 7
    assert styles.count("--app-fert-editor-row-even-bg:") == 7

def test_live_result_bar_uses_consistent_high_visibility_type() -> None:
    styles = read_frontend_file("styles.css")
    index = read_frontend_file("index.html")

    assert "--live-value-size: 1.18rem" in styles
    assert ".live-metric strong" in styles
    assert ".live-ec .ec-value" in styles
    assert ".ion-ratio-pill strong" in styles
    assert "font-size: var(--live-value-size)" in styles
    assert ".live-ec .metric-title,\n.live-ion-ratios .metric-title {\n  margin-bottom: var(--space-2);" in styles
    assert "text-transform: none" in styles
    assert "letter-spacing: 0" in styles
    assert "EC (mS/cm)" in index
    assert 'data-i18n="live.ionRatios"' in index
    assert "Ca:Mg ratio (mg/L)" in index

def test_sidebar_omits_co3_si_ratio_chip() -> None:
    app_js = read_frontend_file("app.js")
    render_block = app_js.split("function renderIonRatios", 1)[1].split("function renderCalculation", 1)[0]

    assert '"CO3:Si"' not in render_block
