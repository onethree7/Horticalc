from tests.frontend_assets import read_frontend_file


def test_calculator_copy_button_present_and_safe_by_default() -> None:
    content = read_frontend_file("index.html")

    assert 'id="copyCalculatorResults"' in content
    assert 'data-i18n="common.copyClipboard" disabled' in content
    assert 'id="copyCalculatorResultsStatus"' in content
    heading = content[content.index('class="block-heading calculator-block-heading"'):]
    heading = heading[:heading.index("</div>\n          </div>")]
    assert heading.index('id="copyCalculatorResults"') < heading.index('id="calculateBtn"')


def test_calculator_copy_report_and_freshness_guard_present() -> None:
    content = read_frontend_file("app/calculator.js")
    notifications = read_frontend_file("app/notifications.js")

    assert "function buildCalculatorClipboardText()" in content
    assert "function copyCalculatorResultsToClipboard()" in content
    assert "function setCalculatorResultCurrent(isCurrent)" in notifications
    assert 't("calculator.clipboardTitle")' in content
    assert 't("calculator.ionBalance")' in content
    assert "setCalculatorResultCurrent(false);" in content
    assert "copyCalculatorButton.disabled = !isCurrent" in notifications
