from __future__ import annotations

from pathlib import Path

import pytest

import horticalc.data_io as data_io
from horticalc.data_io import (
    load_molar_masses,
    load_nutrient_solution_data,
    load_recipe,
    load_water_profile_data,
    save_recipe,
)


@pytest.mark.parametrize("content", ["- item\n", "plain text\n"])
def test_yaml_loaders_require_top_level_mapping(tmp_path: Path, content: str) -> None:
    path = tmp_path / "invalid.yml"
    path.write_text(content, encoding="utf-8")

    with pytest.raises(ValueError, match="must contain a YAML mapping"):
        load_recipe(path)


@pytest.mark.parametrize(
    ("filename", "content", "loader"),
    [
        ("recipe.yml", "name: Test\nliters: .inf\n", load_recipe),
        ("water.yml", "name: Test\nmg_per_l:\n  Ca: .nan\n", load_water_profile_data),
        (
            "solution.yml",
            "name: Test\ntargets_mg_per_l:\n  N_total: .inf\n",
            load_nutrient_solution_data,
        ),
        ("masses.yml", "Ca: .nan\n", load_molar_masses),
    ],
)
def test_yaml_loaders_reject_non_finite_numbers(
    tmp_path: Path,
    filename: str,
    content: str,
    loader,
) -> None:
    path = tmp_path / filename
    path.write_text(content, encoding="utf-8")

    with pytest.raises(ValueError, match="finite numbers"):
        loader(path)


def test_recipe_save_rejects_non_finite_numbers(tmp_path: Path) -> None:
    path = tmp_path / "recipe.yml"

    with pytest.raises(ValueError, match="finite numbers"):
        save_recipe(path, {"name": "Invalid", "liters": float("inf")})

    assert not path.exists()


def test_atomic_yaml_save_preserves_existing_file_on_replace_failure(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    path = tmp_path / "recipe.yml"
    original = "name: Original\nliters: 10\n"
    path.write_text(original, encoding="utf-8")

    def fail_replace(_source: Path, _destination: Path) -> None:
        raise OSError("replace failed")

    monkeypatch.setattr(data_io.os, "replace", fail_replace)

    with pytest.raises(OSError, match="replace failed"):
        save_recipe(path, {"name": "Updated", "liters": 20})

    assert path.read_text(encoding="utf-8") == original
    assert list(tmp_path.glob(".recipe.yml.tmp-*")) == []
