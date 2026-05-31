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
    assert "Erstelle oder lade eigene Dünger" in content
    assert "Konfiguriere deine <span>WASSERWERTE</span>" in content
    assert "Erstelle Rezepte von Hand im <span>RECHNER</span>" in content
    assert "damit der <span>SOLVER</span> die Mengen berechnet" in content
    assert 'class="workflow-step-index"' not in content
    assert "<span>0</span>" not in content
    assert "<span>1</span>" not in content
    assert "<span>2a</span>" not in content
    assert "<span>2b</span>" not in content
    assert 'data-testid="rail-api-controls"' in content
    assert 'data-testid="live-bar"' in content
    assert 'id="liveWaterEc18"' in content
    assert "Wasser EC25" in content
    assert "Wasser EC18" in content
    assert "live-tile--balance" in content
    assert "live-tile--npk" in content
    assert "Hydroponic Solution Calculator and powerful Nutrient Solver." in content
    assert "Nährlösung-Rechner" not in content
    assert "live-tile" in content
    assert content.index('data-testid="rail-brand"') < content.index('data-testid="rail-api-controls"')
    assert content.index('data-testid="rail-api-controls"') < content.index('data-testid="workflow-guide"')
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
    assert ".rail-guide-list" in content
    assert "--app-solver" in content
    assert ".workflow-step.is-active" in content
    assert ".workspace" in content
    assert "overflow-y: auto" in content
    assert ".live-bar" in content
    assert ".live-tile--npk" in content
    assert ".live-tile--balance" in content
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
