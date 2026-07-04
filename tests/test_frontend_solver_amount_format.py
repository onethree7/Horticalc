from tests.frontend_assets import read_frontend_file


def test_fertilizer_amounts_use_adaptive_small_value_formatting() -> None:
    content = read_frontend_file("app.js")

    assert "function formatDoseValue(value)" in content
    assert "const decimals = absValue >= 1 ? 4 : absValue >= 0.01 ? 6 : 8;" in content
    assert "formatDoseDisplay(Number(fert.grams), fert.name)" in content
    assert "doseUnitDefinition(fert.name).symbol" in content


def test_calculator_accepts_and_displays_small_fertilizer_amounts() -> None:
    content = read_frontend_file("app.js")

    assert 'input.step = "any";' in content
    assert "input.value = formatDoseInput(calculatorRow.grams, calculatorRow.name);" in content
    assert "function formatDoseInput(value, fertilizerOrName)" in content
    assert "canonicalDoseToDisplay(value, fertilizerOrName)" in content
    assert 'return formatted === "-" ? "0" : formatted;' in content
