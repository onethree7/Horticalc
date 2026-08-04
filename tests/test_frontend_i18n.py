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
        "theme.tokyoNight",
        "theme.solarizedLight",
        "theme.dracula",
        "theme.gruvboxDark",
        "theme.catppuccinMocha",
        "theme.monokaiClassic",
        "theme.windows95",
        "theme.commodore64",
        "theme.nord",
        "theme.amberCrt",
        "solver.config.relativeWeighting",
        "solver.config.overshootPenalty",
        "solver.config.scaleEpsilon",
        "solver.config.underfillMaxIter",
        "solver.config.nTotalGovernor",
        "solver.modelLabel",
        "solver.model.massNnls",
        "solver.model.hierarchical",
        "solver.model.nnlsTuning",
        "solver.modelMassHint",
        "solver.modelHierarchicalHint",
        "solver.modelNnlsTuningHint",
        "solver.priority.legend",
        "solver.priority.under",
        "solver.priority.over",
        "solver.priority.level1",
        "solver.priority.level4",
        "solver.priority.reportOnly",
        "solver.priority.underAria",
        "solver.priority.overAria",
        "solver.priority.resultSummary",
        "solver.reportOnlyHint",
        "editor.solverMaxDoseHint",
    }

    for locale in LOCALES:
        assert required_keys <= set(_catalog(locale)), locale


def test_nonstandard_solver_models_are_marked_experimental_in_every_locale() -> None:
    markers = {
        "de": "experimentell",
        "en": "experimental",
        "nl": "experimenteel",
        "es": "experimental",
        "zh": "实验性",
    }

    for locale, marker in markers.items():
        catalog = _catalog(locale)
        assert marker in catalog["solver.model.massNnls"].casefold(), locale
        assert marker in catalog["solver.model.hierarchical"].casefold(), locale
        assert marker in catalog["solver.modelMassHint"].casefold(), locale
        assert marker in catalog["solver.modelHierarchicalHint"].casefold(), locale
        assert marker not in catalog["solver.model.nnlsTuning"].casefold(), locale
        assert marker not in catalog["solver.modelNnlsTuningHint"].casefold(), locale
