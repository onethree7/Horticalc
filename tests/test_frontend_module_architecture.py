from __future__ import annotations

import re

from tests.frontend_assets import frontend_app_sources, read_frontend_file

FEATURES = {"calculator", "editor", "history", "profiles", "settings", "shell", "solver", "water"}


def _imports(source: str) -> set[str]:
    return set(re.findall(r'from\s+"\.\.?/([^"?]+\.js)"', source))


def test_feature_modules_export_controller_factories_without_feature_imports() -> None:
    for feature in FEATURES:
        source = read_frontend_file(f"app/{feature}.js")
        assert f"export function create{feature.title()}Controller" in source
        imported_stems = {path.rsplit("/", 1)[-1].removesuffix(".js") for path in _imports(source)}
        assert not (imported_stems & (FEATURES - {feature})), feature


def test_main_is_the_only_composition_root() -> None:
    main = read_frontend_file("app/main.js")
    for feature in FEATURES:
        assert f'from "./{feature}.js"' in main
    assert "window.Horticalc" not in main
    assert "window.HORTICALC" not in main


def test_api_transport_has_no_dom_or_feature_dependency() -> None:
    api = read_frontend_file("app/api.js")
    assert "document." not in api
    assert "querySelector" not in api
    assert not (_imports(api) & {f"{feature}.js" for feature in FEATURES})


def test_removed_global_state_and_monolith_stay_removed() -> None:
    assert "app/state.js" not in frontend_app_sources()
    assert "app/app.js" not in frontend_app_sources()
    combined = "\n".join(read_frontend_file(path) for path in frontend_app_sources())
    assert "window.HorticalcRequestGate" not in combined
    assert "window.HorticalcI18n" not in combined
    assert "window.HORTICALC_I18N" not in combined
