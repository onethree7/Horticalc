from tests.frontend_assets import read_frontend_file


def test_fertilizer_amounts_use_adaptive_small_value_formatting() -> None:
    units = read_frontend_file("app/units.js")
    solver = read_frontend_file("app/solver.js")

    assert "function formatDoseValue(value)" in units
    assert "const decimals = abs >= 1 ? 4 : abs >= 0.01 ? 6 : 8;" in units
    assert "formatDoseDisplay(Number(fert.grams), fert.name)" in solver
    assert "doseUnitDefinition(fert.name).symbol" in solver


def test_calculator_accepts_and_displays_small_fertilizer_amounts() -> None:
    content = read_frontend_file("app/calculator.js")
    units = read_frontend_file("app/units.js")

    assert 'input.type = "text";' in content
    assert 'input.inputMode = "decimal";' in content
    assert "input.value = formatDoseInput(calculatorRow.grams, calculatorRow.name);" in content
    assert "formatDoseInput(value, fertilizer)" in units
    assert "canonicalDoseToDisplay(value, fertilizer)" in units
    assert 'return formatted === "-" ? "0" : formatted;' in units
