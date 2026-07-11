from __future__ import annotations

import re
from pathlib import Path

FRONTEND_DIR = Path(__file__).resolve().parents[1] / "frontend"


def frontend_path(name: str) -> Path:
    return FRONTEND_DIR / name


def frontend_app_sources() -> list[str]:
    index_html = frontend_path("index.html").read_text(encoding="utf-8")
    return re.findall(r'<script\s+src="(app/[^"]+\.js)(?:\?[^\"]*)?"', index_html)


def read_frontend_file(name: str) -> str:
    if name == "app.js":
        return "\n".join(
            frontend_path(source).read_text(encoding="utf-8")
            for source in frontend_app_sources()
        )
    return frontend_path(name).read_text(encoding="utf-8")
