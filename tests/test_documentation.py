from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "docs"
EXPECTED_DOCS = {
    "api.md",
    "architecture.md",
    "cli.md",
    "data-formats.md",
    "ec.md",
    "solver.md",
    "usage.md",
}
ROOT_DOCS = ("README.md", "CONTRIBUTING.md", "RELEASE.md", "SECURITY.md", "AGENTS.md")
OLD_DOCS = {
    "api_reference.md",
    "cli_reference.md",
    "commands.md",
    "data_model.md",
    "decisions.md",
    "development.md",
    "documentation_architecture.md",
    "gui.md",
    "index.md",
    "nutrient_solution_profiles.md",
    "quickstart.md",
    "release_build.md",
    "terminology_style_guide.md",
    "unit_handling.md",
    "user_guide.md",
}
MARKDOWN_LINK = re.compile(r"(?<!!)\[[^]]+\]\(([^)]+)\)")
HEADING = re.compile(r"^#{1,6}\s+(.+?)\s*$", re.MULTILINE)
FENCED_BLOCK = re.compile(r"^```.*?^```[ \t]*$", re.MULTILINE | re.DOTALL)
ENDPOINT_ROW = re.compile(r"^\| `(GET|POST)` \| `(/[^`]+)` \|", re.MULTILINE)
SOURCE_ROUTE = re.compile(r'^@app\.(get|post)\("([^"{]+)"', re.MULTILINE)
PUBLIC_ENDPOINTS = {
    ("GET", "/health"),
    ("GET", "/schema/fertilizer-comp-keys"),
    ("GET", "/schema/solver-config"),
    ("GET", "/schema/units"),
    ("POST", "/calculate"),
    ("POST", "/solve"),
}


def _markdown_files() -> list[Path]:
    return [*(ROOT / name for name in ROOT_DOCS), *sorted(DOCS_DIR.glob("*.md"))]


def _anchors(path: Path) -> set[str]:
    counts: dict[str, int] = {}
    anchors = set()
    prose = FENCED_BLOCK.sub("", path.read_text(encoding="utf-8"))
    for heading in HEADING.findall(prose):
        plain = re.sub(r"[`*_~]", "", heading)
        slug = re.sub(r"[^\w -]", "", plain.casefold()).strip().replace(" ", "-")
        suffix = counts.get(slug, 0)
        counts[slug] = suffix + 1
        anchors.add(slug if suffix == 0 else f"{slug}-{suffix}")
    return anchors


def test_active_document_set_is_intentional() -> None:
    assert {path.name for path in DOCS_DIR.glob("*.md")} == EXPECTED_DOCS


def test_local_markdown_links_and_anchors_resolve() -> None:
    failures = []
    for source in _markdown_files():
        for raw_target in MARKDOWN_LINK.findall(source.read_text(encoding="utf-8")):
            target = unquote(raw_target.strip().strip("<>"))
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            path_text, _, fragment = target.partition("#")
            destination = source if not path_text else (source.parent / path_text).resolve()
            if not destination.exists():
                failures.append(f"{source.relative_to(ROOT)} -> missing {raw_target}")
            elif fragment and destination.suffix.casefold() == ".md" and fragment not in _anchors(destination):
                failures.append(f"{source.relative_to(ROOT)} -> missing anchor {raw_target}")
    assert not failures, "\n".join(failures)


def test_referenced_repository_paths_exist() -> None:
    prefixes = (".github/", "api/", "data/", "docs/", "frontend/", "recipes/", "scripts/", "src/", "tests/")
    root_names = {"AGENTS.md", "CONTRIBUTING.md", "LICENSE", "README.md", "RELEASE.md", "SECURITY.md"}
    failures = []
    for source in _markdown_files():
        for value in re.findall(r"`([^`\n]+)`", source.read_text(encoding="utf-8")):
            if "<" in value or ">" in value or not (value.startswith(prefixes) or value in root_names):
                continue
            matches = list(ROOT.glob(value)) if any(char in value for char in "*?[") else [ROOT / value]
            if not matches or not all(path.exists() for path in matches):
                failures.append(f"{source.relative_to(ROOT)} -> missing repo path {value}")
    assert not failures, "\n".join(failures)


def test_obsolete_documentation_language_is_absent() -> None:
    combined = "\n".join(path.read_text(encoding="utf-8") for path in _markdown_files())
    for old_name in OLD_DOCS:
        assert old_name not in combined
    for stale_text in (
        "Status: `",
        "Wasserwerte",
        "historical report",
        "ALLOWED_TARGET_KEYS` in `src/horticalc/solver.py",
    ):
        assert stale_text not in combined


def test_readme_is_release_first_and_quick() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    quickstart = readme.split("## Quick start", 1)[1].split("## First calculation", 1)[0]
    nonblank_lines = [line for line in quickstart.splitlines() if line.strip()]
    assert len(nonblank_lines) <= 30
    assert readme.index("### Windows installer") < readme.index("### Portable Windows") < readme.index("### Linux")
    assert readme.index("### Linux") < readme.index("run from source")
    assert "releases/latest" in readme


def test_documented_public_api_matches_implemented_subset() -> None:
    api_doc = (DOCS_DIR / "api.md").read_text(encoding="utf-8")
    documented = {(method, path) for method, path in ENDPOINT_ROW.findall(api_doc)}
    source = (ROOT / "api" / "app.py").read_text(encoding="utf-8")
    implemented = {(method.upper(), path) for method, path in SOURCE_ROUTE.findall(source)}
    assert documented == PUBLIC_ENDPOINTS
    assert documented <= implemented
    assert "/docs" in api_doc and "/openapi.json" in api_doc
    assert "not part of the supported external contract" in api_doc
