from tests.frontend_assets import read_frontend_file


def test_ion_summary_has_expandable_nitrogen_columns():
    content = read_frontend_file("app.js")

    assert "N-Σ" in content
    assert "N_NO3" in content
    assert "N_NH4" in content
    assert "N_UREA" in content
    assert "ionNToggle" in content

def test_ion_balance_uses_sum_symbols_for_charge_totals():
    content = read_frontend_file("app.js")

    assert 'cations_meq_per_l: "Σ+"' in content
    assert 'anions_meq_per_l: "Σ-"' in content
    assert 'cations_meq_per_l: "E+"' not in content
    assert 'anions_meq_per_l: "E-"' not in content


def test_fertilizer_amount_header_uses_semantic_mass_symbol():
    app_js = read_frontend_file("app.js")
    styles_css = read_frontend_file("styles.css")

    assert 'document.createElement("var")' in app_js
    assert 'massSymbol.textContent = "m";' in app_js
    assert 'amountHeader.replaceChildren(massSymbol, " [g]");' in app_js
    assert ".quantity-symbol" in styles_css
    assert "font-style: italic;" in styles_css
