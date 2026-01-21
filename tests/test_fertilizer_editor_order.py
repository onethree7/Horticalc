from __future__ import annotations

import re
from pathlib import Path


def _load_preferred_keys() -> list[str]:
    app_js = Path("frontend/app.js").read_text(encoding="utf-8")
    match = re.search(
        r"const\s+fertilizerEditorPreferredKeys\s*=\s*\[(.*?)\];",
        app_js,
        re.DOTALL,
    )
    assert match, "fertilizerEditorPreferredKeys array not found in frontend/app.js"
    entries = re.findall(r'"([^"]+)"', match.group(1))
    return entries


def test_fertilizer_editor_n_form_order() -> None:
    keys = _load_preferred_keys()
    no3_index = keys.index("NO3")
    nh4_index = keys.index("NH4")
    urea_index = keys.index("UREA")
    assert no3_index < nh4_index < urea_index
