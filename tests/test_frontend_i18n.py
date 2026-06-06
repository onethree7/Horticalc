from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"


def _catalog(locale: str) -> dict[str, str]:
    content = (FRONTEND / "i18n" / f"{locale}.js").read_text(encoding="utf-8")
    match = re.search(rf"window\.HORTICALC_I18N\.{locale}\s*=\s*(\{{.*\}});", content, re.S)
    assert match, f"catalog assignment missing for {locale}"
    return json.loads(match.group(1))


def test_i18n_catalogs_exist_and_have_matching_keys() -> None:
    catalogs = {locale: _catalog(locale) for locale in ("de", "en", "nl")}
    base_keys = set(catalogs["de"])

    assert base_keys
    for locale, catalog in catalogs.items():
        assert set(catalog) == base_keys, locale


def test_frontend_loads_i18n_before_app_js() -> None:
    content = (FRONTEND / "index.html").read_text(encoding="utf-8")

    assert 'src="i18n/de.js' in content
    assert 'src="i18n/en.js' in content
    assert 'src="i18n/nl.js' in content
    assert 'src="i18n/runtime.js' in content
    assert content.index('src="i18n/runtime.js') < content.index('src="app.js')


def test_language_selector_persists_frontend_locale() -> None:
    index_html = (FRONTEND / "index.html").read_text(encoding="utf-8")
    runtime_js = (FRONTEND / "i18n" / "runtime.js").read_text(encoding="utf-8")
    app_js = (FRONTEND / "app.js").read_text(encoding="utf-8")

    assert '<select id="languageSelect"' in index_html
    assert 'const DEFAULT_LOCALE = "de";' in runtime_js
    assert 'const LOCALE_STORAGE_KEY = "horticalc.locale";' in runtime_js
    assert "document.documentElement.lang = currentLocale;" in runtime_js
    assert "initializeLanguageControl();" in app_js
    assert 'window.addEventListener("horticalc:localechange", refreshLocalizedUi);' in app_js


def test_frontend_i18n_keeps_data_contract_names_literal() -> None:
    catalogs = {locale: _catalog(locale) for locale in ("de", "en", "nl")}
    app_js = (FRONTEND / "app.js").read_text(encoding="utf-8")

    assert catalogs["de"]["editor.fertilizerName"] == "Düngername"
    assert catalogs["en"]["editor.fertilizerName"] == "Fertilizer name"
    assert catalogs["nl"]["editor.fertilizerName"] == "Meststofnaam"

    assert "fertilizers_allowed" in app_js
    assert "N_total" in app_js
    assert "NO3" in app_js
