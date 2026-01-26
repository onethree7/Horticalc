#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
import unicodedata
from pathlib import Path

DEFAULT_EXTENSIONS = {
    ".css",
    ".html",
    ".js",
    ".md",
    ".py",
    ".toml",
    ".yaml",
    ".yml",
}

EXCLUDE_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "venv",
    ".venv",
}


def iter_files(root: Path, extensions: set[str]) -> list[Path]:
    paths: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in EXCLUDE_DIRS for part in path.parts):
            continue
        if path.suffix.lower() not in extensions:
            continue
        paths.append(path)
    return paths


def find_control_chars(text: str) -> list[tuple[int, int, str, str]]:
    results: list[tuple[int, int, str, str]] = []
    line = 1
    column = 0
    for char in text:
        if char == "\n":
            line += 1
            column = 0
            continue
        column += 1
        if unicodedata.category(char) == "Cf":
            results.append((line, column, char, unicodedata.name(char, "UNKNOWN")))
    return results


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Scan repo text files for hidden/bidi Unicode control characters.",
    )
    parser.add_argument(
        "root",
        nargs="?",
        default=".",
        help="Root directory to scan (default: current directory).",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    matches = []
    for path in iter_files(root, DEFAULT_EXTENSIONS):
        text = path.read_text(encoding="utf-8")
        violations = find_control_chars(text)
        if violations:
            matches.append((path, violations))

    if matches:
        print("Found Unicode control characters (category Cf):")
        for path, violations in matches:
            rel_path = path.relative_to(root)
            for line, column, char, name in violations:
                print(
                    f"- {rel_path}:{line}:{column} U+{ord(char):04X} {name}"
                )
        return 1

    print("No Unicode control characters found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
