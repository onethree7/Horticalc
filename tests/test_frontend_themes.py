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

    for theme in ("commodore-64", "game-boy-dmg"):
        block = _theme_block(css, theme)
        assert "--app-overlay-bg: none;" in block
        assert "--app-overlay-opacity: 0;" in block

    amber = _theme_block(css, "amber-crt")
    assert "--app-overlay-opacity: 0.042;" in amber

    game_boy = _theme_block(css, "game-boy-dmg")
    assert '--app-font-family: inter, "Segoe UI", system-ui, sans-serif;' in game_boy
    assert "--app-muted: #0f380f;" in game_boy
    assert "--app-body-bg: #0f380f;" in game_boy
    assert "--app-shell-bg: #306230;" in game_boy
    assert "--app-rail-bg: #306230;" in game_boy
    assert "--app-solver-step-active-bg: #0f380f;" in game_boy
