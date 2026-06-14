from tests.frontend_assets import read_frontend_file


def test_fertilizer_amounts_use_adaptive_small_value_formatting() -> None:
    content = read_frontend_file("app.js")

    assert 'const fertilizerTraceFormatter = new Intl.NumberFormat("en-US", {' in content
    assert "maximumFractionDigits: 4" in content
    assert "function formatFertilizerGrams(value)" in content
    assert 'return formatted === "0" ? "<0.0001" : formatted;' in content
    assert "gramsCell.textContent = formatFertilizerGrams(Number(fert.grams));" in content
    assert "formatFertilizerGrams(Number(fert.grams))," in content


def test_calculator_accepts_and_displays_small_fertilizer_amounts() -> None:
    content = read_frontend_file("app.js")

    assert 'input.step = "any";' in content
    assert "input.value = formatFertilizerGramsInput(fertilizerAmounts[i]);" in content
    assert "function formatFertilizerGramsInput(value)" in content
    assert 'return formatted === "0" ? String(numericValue) : formatted;' in content
