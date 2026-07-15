from __future__ import annotations

import re
from pathlib import Path

FRONTEND_DIR = Path(__file__).resolve().parents[1] / "frontend"


def frontend_path(name: str) -> Path:
    return FRONTEND_DIR / name


def frontend_app_sources() -> list[str]:
    return sorted(path.relative_to(FRONTEND_DIR).as_posix() for path in (FRONTEND_DIR / "app").glob("*.js"))


def frontend_module_entry() -> str:
    index_html = frontend_path("index.html").read_text(encoding="utf-8")
    match = re.search(
        r'<script\s+type="module"\s+src="([^"]+\.js)(?:\?[^\"]*)?"',
        index_html,
    )
    assert match, "frontend module entrypoint missing"
    return match.group(1)


def read_frontend_file(name: str) -> str:
    return frontend_path(name).read_text(encoding="utf-8")
