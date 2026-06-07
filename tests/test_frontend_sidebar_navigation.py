from tests.frontend_assets import read_frontend_file


def test_sidebar_uses_primary_workflow_menu_with_collapsible_guide() -> None:
    content = read_frontend_file("index.html")

    workflow_block = content.split('data-testid="workflow-nav"', 1)[1].split("</section>", 1)[0]

    assert 'data-i18n="workflow.menu"' in workflow_block
    assert 'class="workflow-step-index"' in workflow_block
    assert 'class="workflow-step-hint"' in workflow_block
    assert '<details class="rail-guide" data-testid="workflow-guide">' in workflow_block
    assert 'data-i18n="workflow.shortGuide"' in workflow_block
    assert '<section class="rail-card rail-guide"' not in content

def test_sidebar_navigation_styles_wrap_button_text() -> None:
    content = read_frontend_file("styles.css")

    assert ".workflow-step-title,\n.workflow-step-hint,\n.workflow-step-arrow" in content
    assert "overflow-wrap: anywhere;" in content
    assert ".rail-brand,\n  .rail-workflow {\n    grid-column: 1 / -1;" in content
