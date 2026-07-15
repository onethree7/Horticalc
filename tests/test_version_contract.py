from __future__ import annotations

import subprocess
import sys
from importlib.metadata import version
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api.app import app
from horticalc import __version__
from scripts.check_release_version import expected_release_tag, validate_release_tag

ROOT = Path(__file__).resolve().parents[1]


def test_runtime_package_api_and_cli_versions_match() -> None:
    assert __version__ == "0.6.0"
    assert version("horticalc") == __version__
    assert TestClient(app).get("/openapi.json").json()["info"]["version"] == __version__
    result = subprocess.run(
        [sys.executable, "-m", "horticalc", "--version"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.stdout.strip() == __version__


def test_release_tag_must_match_the_single_version_literal() -> None:
    assert expected_release_tag() == "v0.6.0"
    validate_release_tag("v0.6.0")
    with pytest.raises(ValueError, match="must be exactly v0.6.0"):
        validate_release_tag("v4.1")
