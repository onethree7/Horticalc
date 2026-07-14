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

def test_i18n_catalogs_exist_and_have_matching_keys() -> None:
    catalogs = {locale: _catalog(locale) for locale in LOCALES}
    base_keys = set(catalogs["de"])

    assert base_keys
    for locale, catalog in catalogs.items():
        assert set(catalog) == base_keys, locale

def test_frontend_imports_i18n_through_the_module_graph() -> None:
    index = read_frontend_file("index.html")
    runtime = read_frontend_file("i18n/runtime.js")
    main = read_frontend_file("app/main.js")
    assert index.count('type="module"') == 1
    assert 'src="app/main.js' in index
    for locale in LOCALES:
        assert f'import {locale} from "./{locale}.js";' in runtime
    assert 'from "../i18n/runtime.js"' in main

def test_language_selector_detects_and_persists_frontend_locale() -> None:
    index_html = read_frontend_file("index.html")
    runtime_js = read_frontend_file("i18n/runtime.js")
    settings = read_frontend_file("app/settings.js")
    main = read_frontend_file("app/main.js")

    assert '<select id="languageSelect"' in index_html
    assert 'const DEFAULT_LOCALE = "en";' in runtime_js
    assert 'const LOCALE_STORAGE_KEY = "horticalc.locale";' in runtime_js
    assert "detectBrowserLocale" in runtime_js
    assert "navigator.languages" in runtime_js
    assert "document.documentElement.lang = currentLocale;" in runtime_js
    assert "dataset.i18nCount" in runtime_js
    assert "i18n.onLocaleChange" in settings
    assert "persistPreferences({ locale: i18n.getLocale() });" in settings
    assert "preferences.locale" in settings
    assert "onLocaleChange: refreshLocalizedUi" in main


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
    app_js = read_frontend_file("app/calculator.js") + read_frontend_file("app/solver.js")

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
    app_js = read_frontend_file("app/calculator.js")

    assert catalogs["de"]["common.productType"] == "Typ"
    assert catalogs["de"]["editor.densityFactor"] == "Dichte [g/mL] / Faktor"
    assert '{ labelKey: "common.productType", label: t("common.productType") }' in app_js
    assert '{ labelKey: "editor.densityFactor", label: t("editor.densityFactor") }' in app_js
