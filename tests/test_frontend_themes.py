from __future__ import annotations

import re

from api.app import THEME_OPTIONS
from tests.frontend_assets import frontend_path


def _theme_block(css: str, theme: str) -> str:
    match = re.search(rf'\.app-body\[data-theme="{re.escape(theme)}"\]\s*\{{([^}}]*)\}}', css)
    assert match, theme
    return match.group(1)


def test_theme_contract_is_synchronized_and_token_only() -> None:
    constants = frontend_path("app/constants.js").read_text(encoding="utf-8")
    markup = frontend_path("index.html").read_text(encoding="utf-8")
    css = frontend_path("styles/themes.css").read_text(encoding="utf-8")

    for theme in THEME_OPTIONS:
        assert f'"{theme}"' in constants
        assert f'value="{theme}"' in markup
        assert f'[data-theme="{theme}"]' in css or theme == "horticalc-dark"

    themed_component_selector = re.compile(r'\[data-theme="[^"]+"\]\s+[.#\[]')
    assert not themed_component_selector.search(css)


def test_retro_screen_effects_favor_readability() -> None:
    css = frontend_path("styles/themes.css").read_text(encoding="utf-8")

    amber = _theme_block(css, "amber-crt")
    assert "--app-overlay-opacity: 0.042;" in amber
