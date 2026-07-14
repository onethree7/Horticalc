from tests.frontend_assets import read_frontend_file


def test_ion_summary_has_expandable_nitrogen_columns():
    content = read_frontend_file("app/constants.js") + read_frontend_file("app/water.js")

    assert 'ionHeaderLabelKey: "solver.nTotal"' in content
    assert "N_NO3" in content
    assert "N_NH4" in content
    assert "N_UREA" in content
    assert "ionNToggle" in content

def test_ion_balance_uses_sum_symbols_for_charge_totals():
    content = read_frontend_file("app/water.js")

    assert 'cations_meq_per_l: t("calculator.ionBalance.cations")' in content
    assert 'anions_meq_per_l: t("calculator.ionBalance.anions")' in content
    assert 'cations_meq_per_l: "E+"' not in content
    assert 'anions_meq_per_l: "E-"' not in content


def test_fertilizer_editor_weight_header_explains_density_and_factor():
    editor = read_frontend_file("app/editor.js")
    calculator = read_frontend_file("app/calculator.js")

    assert 'fertilizerEditorHeader("Density / factor", "weight_factor", "editor.densityFactor")' in editor
    assert '{ labelKey: "common.amount", label: t("common.amount") }' in calculator
    assert 'massHeaderButton.replaceChildren' not in calculator
