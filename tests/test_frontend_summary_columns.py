from pathlib import Path


def test_ion_summary_has_expandable_nitrogen_columns():
    app_js = Path(__file__).resolve().parents[1] / "frontend" / "app.js"
    content = app_js.read_text(encoding="utf-8")

    assert "N-Σ" in content
    assert "N_NO3" in content
    assert "N_NH4" in content
    assert "N_UREA" in content
    assert "ionNToggle" in content
