from __future__ import annotations

import json
import re

from api.app import PREFERENCE_OPTIONS
from tests.frontend_assets import frontend_path


def _theme_block(css: str, theme: str) -> str:
    match = re.search(rf'\.app-body\[data-theme="{re.escape(theme)}"\]\s*\{{([^}}]*)\}}', css)
    assert match, theme
    return match.group(1)


def test_theme_contract_is_synchronized_and_token_only() -> None:
    constants = frontend_path("app/constants.js").read_text(encoding="utf-8")
    markup = frontend_path("index.html").read_text(encoding="utf-8")
    css = frontend_path("styles/themes.css").read_text(encoding="utf-8")
    preferences = json.loads(frontend_path("preferences.json").read_text(encoding="utf-8"))

    assert preferences == {
        "default_theme": PREFERENCE_OPTIONS["default_theme"],
        "default_ui_scale": PREFERENCE_OPTIONS["default_ui_scale"],
        "themes": PREFERENCE_OPTIONS["themes"],
        "ui_scales": PREFERENCE_OPTIONS["ui_scales"],
        "locales": PREFERENCE_OPTIONS["locales"],
    }
    for theme in preferences["themes"]:
        assert constants.count(f'"{theme}"') == (1 if theme == preferences["default_theme"] else 0)
        assert f'value="{theme}"' not in markup
        assert f'[data-theme="{theme}"]' in css or theme == "horticalc-dark"

    assert 'id="themeSelect"' in markup
    assert 'id="languageSelect"' in markup
    assert 'id="uiScaleSelect"' in markup

    themed_component_selector = re.compile(r'\[data-theme="[^"]+"\]\s+[.#\[]')
    assert not themed_component_selector.search(css)


def test_retro_screen_effects_favor_readability() -> None:
    css = frontend_path("styles/themes.css").read_text(encoding="utf-8")

    amber = _theme_block(css, "amber-crt")
    assert "--app-overlay-opacity: 0.042;" in amber
