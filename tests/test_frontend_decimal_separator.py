from tests.frontend_assets import read_frontend_file


def test_frontend_accepts_comma_input_and_normalizes_to_dot() -> None:
    app_js = read_frontend_file("app.js")
    index_html = read_frontend_file("index.html")

    assert 'const n = Number(s.replace(",", "."));' in app_js
    assert "function normalizeDecimalInputElement(input, value, fallback = \"0\")" in app_js
    assert 'input.type = "number";' not in app_js
    assert 'type="number"' not in index_html
    assert 'inputmode="decimal"' in index_html


def test_frontend_number_formatting_is_decimal_dot_only() -> None:
    app_js = read_frontend_file("app.js")

    assert 'const numberFormatter = new Intl.NumberFormat("en-US", {' in app_js
    assert 'const formatter = new Intl.NumberFormat("en-US", {' in app_js
    assert "new Intl.NumberFormat(i18n.getLocale()" not in app_js
    assert "useGrouping: false" in app_js
