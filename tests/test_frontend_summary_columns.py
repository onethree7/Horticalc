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
