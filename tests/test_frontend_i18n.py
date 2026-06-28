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
    assert content.index('src="i18n/runtime.js') < content.index('src="app.js')

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
    assert "initializeLanguageControl();" in app_js
    assert "persistPreferences({ locale: i18n.getLocale() });" in app_js
    assert "preferences.locale" in app_js
    assert 'window.addEventListener("horticalc:localechange", refreshLocalizedUi);' in app_js

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


def test_fertilizer_dose_header_covers_solids_and_liquids() -> None:
    catalogs = {locale: _catalog(locale) for locale in LOCALES}
    index_html = read_frontend_file("index.html")

    assert catalogs["de"]["common.grams"] == "Gramm/ml"
    assert catalogs["en"]["common.grams"] == "Grams/ml"
    assert catalogs["nl"]["common.grams"] == "Gram/ml"
    assert catalogs["es"]["common.grams"] == "Gramos/ml"
    assert catalogs["zh"]["common.grams"] == "克/毫升"
    assert '<th data-i18n="common.grams">Grams/ml</th>' in index_html


def test_calculator_fertilizer_metadata_uses_clear_labels() -> None:
    catalogs = {locale: _catalog(locale) for locale in LOCALES}
    app_js = read_frontend_file("app.js")

    assert catalogs["de"]["common.productType"] == "Typ"
    assert catalogs["de"]["common.mass"] == "Masse"
    assert '{ labelKey: "common.productType", label: "Type" }' in app_js
    assert '{ labelKey: "common.mass", label: "Mass" }' in app_js
