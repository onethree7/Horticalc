from __future__ import annotations

from pathlib import Path

import pytest

import horticalc.data_io as data_io
from horticalc.data_io import (
    load_molar_masses,
    load_nutrient_solution_data,
    load_recipe,
    load_water_profile_data,
    save_nutrient_solution,
    save_recipe,
)


@pytest.mark.parametrize("content", ["- item\n", "plain text\n"])
def test_yaml_loaders_require_top_level_mapping(tmp_path: Path, content: str) -> None:
    path = tmp_path / "invalid.yml"
    path.write_text(content, encoding="utf-8")

    with pytest.raises(ValueError, match="must contain a YAML mapping"):
        load_recipe(path)


def test_yaml_loader_rejects_aliases_before_recursive_validation(tmp_path: Path) -> None:
    path = tmp_path / "cyclic.yml"
    path.write_text("root: &root\n  self: *root\n", encoding="utf-8")

    with pytest.raises(data_io.yaml.YAMLError, match="aliases are not supported"):
        load_recipe(path)


def test_yaml_loader_rejects_excessive_nesting(tmp_path: Path) -> None:
    path = tmp_path / "deep.yml"
    path.write_text("value: " + "[" * 70 + "0" + "]" * 70, encoding="utf-8")

    with pytest.raises(data_io.yaml.YAMLError, match="nesting is too deep"):
        load_recipe(path)


def test_yaml_loader_rejects_oversized_files(tmp_path: Path) -> None:
    path = tmp_path / "large.yml"
    path.write_text("value: " + "x" * data_io.MAX_YAML_BYTES, encoding="utf-8")

    with pytest.raises(ValueError, match="YAML limit"):
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


@pytest.mark.parametrize(
    ("content", "loader", "message"),
    [
        ("name: Invalid\nmg_per_l: []\n", load_water_profile_data, "must be a mapping"),
        (
            'name: Invalid\nosmosis_percent: ""\nmg_per_l: {}\n',
            load_water_profile_data,
            "must be numeric",
        ),
        (
            "name: Invalid\ntargets_mg_per_l: []\n",
            load_nutrient_solution_data,
            "must be a mapping",
        ),
    ],
)
def test_profile_loaders_reject_explicitly_malformed_empty_values(
    tmp_path: Path,
    content: str,
    loader,
    message: str,
) -> None:
    path = tmp_path / "invalid.yml"
    path.write_text(content, encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        loader(path)


@pytest.mark.parametrize(
    ("content", "loader", "message"),
    [
        ("name: Invalid\nmg_per_l:\n  Ca: -1\n", load_water_profile_data, "must be >= 0"),
        (
            "name: Invalid\ntargets_mg_per_l:\n  K: -1\n",
            load_nutrient_solution_data,
            "must be >= 0",
        ),
        ("name: Invalid\nosmosis_percent: 101\nmg_per_l: {}\n", load_water_profile_data, "between 0 and 100"),
        ("Ca: 0\n", load_molar_masses, "must be > 0"),
    ],
)
def test_profile_loaders_enforce_domain_bounds(
    tmp_path: Path,
    content: str,
    loader,
    message: str,
) -> None:
    path = tmp_path / "invalid.yml"
    path.write_text(content, encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        loader(path)


def test_recipe_save_rejects_non_finite_numbers(tmp_path: Path) -> None:
    path = tmp_path / "recipe.yml"

    with pytest.raises(ValueError, match="finite numbers"):
        save_recipe(path, {"name": "Invalid", "liters": float("inf")})

    assert not path.exists()


def test_nutrient_solution_persists_solver_priorities(tmp_path: Path) -> None:
    path = tmp_path / "prioritized.yml"
    solver_config = {
        "solver_model": "hierarchical",
        "target_priorities": {
            "N_total": {"under": 1, "over": 1},
            "Ca": {"under": 2, "over": 4},
        },
    }

    save_nutrient_solution(
        path,
        name="Prioritized",
        source="Test",
        targets_mg_per_l={"N_total": 160.0, "Ca": 120.0},
        solver_config=solver_config,
    )

    assert load_nutrient_solution_data(path) == {
        "name": "Prioritized",
        "source": "Test",
        "targets_mg_per_l": {"N_total": 160.0, "Ca": 120.0},
        "solver_config": solver_config,
    }


def test_nutrient_solution_writer_uses_strict_canonical_boolean_contract(tmp_path: Path) -> None:
    path = tmp_path / "invalid.yml"

    with pytest.raises(ValueError, match="urea_as_nh4 must be a boolean"):
        save_nutrient_solution(
            path,
            name="Invalid",
            source="Test",
            targets_mg_per_l={"K": 100},
            urea_as_nh4="false",  # type: ignore[arg-type]
        )

    assert not path.exists()


def test_nutrient_solution_loader_detects_duplicates_after_name_normalization(tmp_path: Path) -> None:
    path = tmp_path / "duplicate.yml"
    path.write_text(
        "name: Duplicate\ntargets_mg_per_l: {K: 100}\nfertilizers_allowed: [A, ' A ']\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="must not contain duplicates"):
        load_nutrient_solution_data(path)


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
