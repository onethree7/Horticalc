from pathlib import Path


def test_icon_button_classes_applied_to_compact_controls():
    index_html = Path(__file__).resolve().parents[1] / "frontend" / "index.html"
    content = index_html.read_text(encoding="utf-8")

    assert 'id="addFertilizerRow" class="btn btn--outline btn--icon icon-button"' in content
    assert 'id="removeFertilizerRow" class="btn btn--outline btn--icon icon-button"' in content
    assert 'id="calculatorScaleDown" class="btn btn--outline btn--icon icon-button"' in content
    assert 'id="calculatorScaleUp" class="btn btn--outline btn--icon icon-button"' in content
    assert 'id="solverTargetScaleDown" class="btn btn--outline btn--icon icon-button"' in content
    assert 'id="solverTargetScaleUp" class="btn btn--outline btn--icon icon-button"' in content
    assert 'id="fertEditorAddRow" class="btn btn--outline btn--icon icon-button"' in content
    assert 'id="fertEditorDeleteRow" class="btn btn--outline btn--icon icon-button"' in content


def test_icon_button_styles_are_scoped():
    styles_css = Path(__file__).resolve().parents[1] / "frontend" / "styles.css"
    content = styles_css.read_text(encoding="utf-8")

    assert ".inline-actions .icon-button" in content
