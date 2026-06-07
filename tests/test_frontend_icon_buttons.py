from tests.frontend_assets import read_frontend_file


def test_icon_button_classes_applied_to_compact_controls():
    content = read_frontend_file("index.html")

    assert 'id="addFertilizerRow" class="btn btn--outline btn--icon icon-button"' in content
    assert 'id="removeFertilizerRow" class="btn btn--outline btn--icon icon-button"' in content
    assert 'id="calculatorScaleDown" class="btn btn--outline btn--icon icon-button"' in content
    assert 'id="calculatorScaleUp" class="btn btn--outline btn--icon icon-button"' in content
    assert 'id="solverTargetScaleDown" class="btn btn--outline btn--icon icon-button"' in content
    assert 'id="solverTargetScaleUp" class="btn btn--outline btn--icon icon-button"' in content
    assert 'id="fertEditorAddRow" class="btn btn--outline btn--icon icon-button"' in content
    assert 'id="fertEditorDeleteRow" class="btn btn--outline btn--icon icon-button"' in content

def test_icon_button_styles_are_scoped():
    content = read_frontend_file("styles.css")

    assert ".inline-actions .icon-button" in content
