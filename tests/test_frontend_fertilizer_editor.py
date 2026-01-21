from pathlib import Path


def test_fertilizer_editor_hco3_column_rightmost() -> None:
    app_js = Path(__file__).resolve().parents[1] / "frontend" / "app.js"
    contents = app_js.read_text(encoding="utf-8")

    assert 'allKeys.indexOf("HCO3")' in contents
    assert 'allKeys.push("HCO3")' in contents
