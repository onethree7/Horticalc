from pathlib import Path


def test_sidebar_uses_primary_workflow_menu_with_collapsible_guide() -> None:
    index_html = Path(__file__).resolve().parents[1] / "frontend" / "index.html"
    content = index_html.read_text(encoding="utf-8")

    workflow_block = content.split('data-testid="workflow-nav"', 1)[1].split("</section>", 1)[0]

    assert "Hauptmenü" in workflow_block
    assert 'class="workflow-step-index"' in workflow_block
    assert 'class="workflow-step-hint"' in workflow_block
    assert '<details class="rail-guide" data-testid="workflow-guide">' in workflow_block
    assert "<summary>Ablauf kurz</summary>" in workflow_block
    assert '<section class="rail-card rail-guide"' not in content


def test_sidebar_navigation_styles_wrap_button_text() -> None:
    styles_css = Path(__file__).resolve().parents[1] / "frontend" / "styles.css"
    content = styles_css.read_text(encoding="utf-8")

    assert ".workflow-step-title,\n.workflow-step-hint,\n.workflow-step-arrow" in content
    assert "overflow-wrap: anywhere;" in content
    assert ".rail-brand,\n  .rail-workflow {\n    grid-column: 1 / -1;" in content
