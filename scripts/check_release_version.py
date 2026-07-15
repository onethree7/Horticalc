"""Validate release tags against the package version."""

from __future__ import annotations

import argparse
import os

from horticalc import __version__


def expected_release_tag() -> str:
    return f"v{__version__}"


def validate_release_tag(tag: str) -> None:
    expected = expected_release_tag()
    if tag != expected:
        raise ValueError(f"Release tag must be exactly {expected}, got {tag!r}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", help="Explicit tag to validate instead of GitHub environment metadata")
    args = parser.parse_args()

    tag = args.tag
    if tag is None and os.environ.get("GITHUB_REF_TYPE") == "tag":
        tag = os.environ.get("GITHUB_REF_NAME", "")
    if tag is not None:
        validate_release_tag(tag)
    print(__version__)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
