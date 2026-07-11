from __future__ import annotations

import json
import re

from tests.frontend_assets import frontend_path, read_frontend_file


LOCALES = ("de", "en", "nl", "es", "zh")

def _catalog(locale: str) -> dict[str, str]:
    content = frontend_path(f"i18n/{locale}.js").read_text(encoding="utf-8")
    match = re.search(rf"window\.HORTICALC_I18N\.{locale}\s*=\s*(\{{.*\}});", content, re.S)
    assert match, f"catalog assignment missing for {locale}"
    return json.loads(match.group(1))

def test_i18n_catalogs_exist_and_have_matching_keys() -> None:
    catalogs = {locale: _catalog(locale) for locale in LOCALES}
    base_keys = set(catalogs["de"])

    assert base_keys
    for locale, catalog in catalogs.items():
        assert set(catalog) == base_keys, locale

def test_frontend_loads_i18n_before_app_js() -> None:
    content = read_frontend_file("index.html")

    assert 'src="i18n/de.js' in content
    assert 'src="i18n/en.js' in content
    assert 'src="i18n/nl.js' in content
    assert 'src="i18n/es.js' in content
    assert 'src="i18n/zh.js' in content
    assert 'src="i18n/runtime.js' in content
    assert content.index('src="i18n/zh.js') < content.index('src="i18n/runtime.js')
    assert content.index('src="i18n/runtime.js') < content.index('src="app/app.js')

def test_language_selector_detects_and_persists_frontend_locale() -> None:
    index_html = read_frontend_file("index.html")
    runtime_js = read_frontend_file("i18n/runtime.js")
    app_js = read_frontend_file("app.js")

    assert '<select id="languageSelect"' in index_html
    assert 'const DEFAULT_LOCALE = "en";' in runtime_js
    assert 'const LOCALE_STORAGE_KEY = "horticalc.locale";' in runtime_js
    assert "detectBrowserLocale" in runtime_js
    assert "navigator.languages" in runtime_js
    assert "document.documentElement.lang = currentLocale;" in runtime_js
    assert "dataset.i18nCount" in runtime_js
    assert "initializeLanguageControl();" in app_js
    assert "persistPreferences({ locale: i18n.getLocale() });" in app_js
    assert "preferences.locale" in app_js
    assert 'window.addEventListener("horticalc:localechange", refreshLocalizedUi);' in app_js


def test_all_catalogs_have_new_localization_keys() -> None:
    catalogs = {locale: _catalog(locale) for locale in LOCALES}
    keys = [
        "status.apiReady",
        "status.activeCount",
        "live.ec",
        "live.npkPNorm",
        "common.ec",
        "common.percent",
        "common.delta",
        "theme.horticalcDark",
        "theme.horticalcLight",
        "theme.highContrast",
        "theme.soil",
        "theme.gchClassic",
        "theme.vtGreen",
        "theme.blueMatrix",
        "solver.config.relativeWeighting",
        "solver.config.overshootPenalty",
        "solver.config.scaleEpsilon",
        "solver.config.singletonOvershootPass",
        "solver.config.singletonShare",
        "solver.config.singletonMaxRegress",
        "solver.config.singletonUnderfillPass",
        "solver.config.underfillShare",
        "solver.config.underfillMaxIter",
        "solver.config.nTotalGovernor",
        "solver.config.nGovernorWeight",
        "solver.nTotal",
        "solver.nNo3",
        "solver.nNh4",
        "solver.nUrea",
        "calculator.ionBalance.cations",
        "calculator.ionBalance.anions",
        "calculator.ionBalance.cbeRaw",
        "calculator.ionBalance.dinRaw",
        "aria.addFertilizerRow",
        "aria.removeFertilizerRow",
        "aria.addFertilizerEditorRow",
        "aria.deleteFertilizerEditorRow",
        "aria.scaleDown",
        "aria.scaleUp",
    ]
    for locale, catalog in catalogs.items():
        for key in keys:
            assert key in catalog, (locale, key)

def test_frontend_i18n_keeps_data_contract_names_literal() -> None:
    catalogs = {locale: _catalog(locale) for locale in LOCALES}
    app_js = read_frontend_file("app.js")

    assert catalogs["de"]["editor.fertilizerName"] == "Düngername"
    assert catalogs["en"]["editor.fertilizerName"] == "Fertilizer name"
    assert catalogs["nl"]["editor.fertilizerName"] == "Meststofnaam"
    assert catalogs["es"]["editor.fertilizerName"] == "Nombre del fertilizante"
    assert catalogs["zh"]["editor.fertilizerName"] == "肥料名称"

    assert "fertilizers_allowed" in app_js
    assert "N_total" in app_js
    assert "NO3" in app_js


def test_fertilizer_dose_header_uses_row_specific_units() -> None:
    catalogs = {locale: _catalog(locale) for locale in LOCALES}
    index_html = read_frontend_file("index.html")

    assert catalogs["de"]["common.amount"] == "Menge"
    assert catalogs["en"]["common.amount"] == "Amount"
    assert '<th data-i18n="common.amount">Amount</th>' in index_html
    assert 'id="configSolidDoseUnit"' in index_html
    assert 'id="configLiquidDoseUnit"' in index_html


def test_calculator_fertilizer_metadata_uses_clear_labels() -> None:
    catalogs = {locale: _catalog(locale) for locale in LOCALES}
    app_js = read_frontend_file("app.js")

    assert catalogs["de"]["common.productType"] == "Typ"
    assert catalogs["de"]["editor.densityFactor"] == "Dichte [g/mL] / Faktor"
    assert '{ labelKey: "common.productType", label: "Type" }' in app_js
    assert '{ labelKey: "editor.densityFactor", label: "Density / factor" }' in app_js
