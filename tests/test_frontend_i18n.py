from __future__ import annotations

import json
import re

from tests.frontend_assets import frontend_path

LOCALES = ("de", "en", "nl", "es", "zh")


def _catalog(locale: str) -> dict[str, str]:
    content = frontend_path(f"i18n/{locale}.js").read_text(encoding="utf-8")
    match = re.search(r"export default\s*(\{.*\});", content, re.S)
    assert match, f"catalog export missing for {locale}"
    return json.loads(match.group(1))


def test_i18n_catalogs_have_matching_nonempty_keys() -> None:
    catalogs = {locale: _catalog(locale) for locale in LOCALES}
    base_keys = set(catalogs["en"])

    assert base_keys
    assert all(set(catalog) == base_keys for catalog in catalogs.values())
    assert all(all(value.strip() for value in catalog.values()) for catalog in catalogs.values())


def test_i18n_catalogs_cover_the_supported_themes_and_solver_labels() -> None:
    required_keys = {
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
        "solver.config.underfillMaxIter",
        "solver.config.nTotalGovernor",
    }

    for locale in LOCALES:
        assert required_keys <= set(_catalog(locale)), locale
