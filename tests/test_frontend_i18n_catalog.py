from __future__ import annotations

import json
import re

from tests.frontend_assets import frontend_path, read_frontend_file

LOCALES = ("de", "en", "nl", "es", "zh")


def _catalog(locale: str) -> dict[str, str]:
    content = frontend_path(f"i18n/{locale}.js").read_text(encoding="utf-8")
    match = re.search(r"export default\s*(\{.*\});", content, re.S)
    assert match, f"catalog export missing for {locale}"
    return json.loads(match.group(1))


def _catalog_values() -> set[str]:
    """Return all values that occur in the English catalog."""
    return set(_catalog("en").values())


def _catalog_keys() -> set[str]:
    return set(_catalog("en").keys())


def test_hardcoded_clipboard_and_summary_strings_are_localized():
    app_js = "\n".join(
        read_frontend_file(path)
        for path in ("app/calculator.js", "app/constants.js", "app/solver.js", "app/water.js")
    )

    hardcoded = [
        '"NPK P-Norm"',
        '"EC (mS/cm)"',
        '"Σ+"',
        '"Σ-"',
        '"CBE-raw"',
        '"DIN-raw"',
        '"N-Σ"',
    ]
    for string in hardcoded:
        assert string not in app_js, string

    localized = [
        't("live.npkPNorm")',
        't("live.ec")',
        't("common.ec")',
        't("calculator.ionBalance.cations")',
        't("calculator.ionBalance.anions")',
        't("calculator.ionBalance.cbeRaw")',
        't("calculator.ionBalance.dinRaw")',
        't("solver.nTotal")',
        't("solver.nNo3")',
        't("solver.nNh4")',
        't("solver.nUrea")',
        "ionHeaderLabelKey: \"solver.nTotal\"",
        "oxideHeaderLabelKey: \"solver.nTotal\"",
    ]
    for snippet in localized:
        assert snippet in app_js, snippet


def test_hardcoded_index_html_strings_are_localized():
    index_html = read_frontend_file("index.html")

    localized_keys = [
        'data-i18n="status.apiReady"',
        'data-i18n="status.activeCount"',
        'data-i18n="live.ec"',
        'data-i18n="common.delta"',
        'data-i18n="common.percent"',
        'data-i18n="theme.horticalcDark"',
        'data-i18n="theme.horticalcLight"',
        'data-i18n="theme.highContrast"',
        'data-i18n="theme.soil"',
        'data-i18n="theme.gchClassic"',
        'data-i18n="theme.vtGreen"',
        'data-i18n="theme.blueMatrix"',
        'data-i18n="solver.config.relativeWeighting"',
        'data-i18n="solver.config.overshootPenalty"',
        'data-i18n="solver.config.scaleEpsilon"',
        'data-i18n="solver.config.singletonOvershootPass"',
        'data-i18n="solver.config.singletonShare"',
        'data-i18n="solver.config.singletonMaxRegress"',
        'data-i18n="solver.config.singletonUnderfillPass"',
        'data-i18n="solver.config.underfillShare"',
        'data-i18n="solver.config.underfillMaxIter"',
        'data-i18n="solver.config.nTotalGovernor"',
        'data-i18n="solver.config.nGovernorWeight"',
        'data-i18n-aria-label="aria.addFertilizerRow"',
        'data-i18n-aria-label="aria.removeFertilizerRow"',
        'data-i18n-aria-label="aria.addFertilizerEditorRow"',
        'data-i18n-aria-label="aria.deleteFertilizerEditorRow"',
        'data-i18n-aria-label="aria.scaleDown"',
        'data-i18n-aria-label="aria.scaleUp"',
        'data-i18n-title="aria.addFertilizerRow"',
        'data-i18n-title="aria.removeFertilizerRow"',
        'data-i18n-title="aria.addFertilizerEditorRow"',
        'data-i18n-title="aria.deleteFertilizerEditorRow"',
        'data-i18n-title="aria.scaleDown"',
        'data-i18n-title="aria.scaleUp"',
    ]
    for snippet in localized_keys:
        assert snippet in index_html, snippet

    # Bare hardcoded phrases that should no longer be in index.html without i18n
    assert "API bereit" not in index_html
    assert "0 aktiv" not in index_html
    assert "Delta %" not in index_html


def test_no_duplicate_catalog_keys_between_files():
    for locale in LOCALES:
        catalog = _catalog(locale)
        assert len(catalog) == len(set(catalog.keys()))
