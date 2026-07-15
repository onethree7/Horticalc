from __future__ import annotations

import csv
from hashlib import sha256
from pathlib import Path

import pytest

import horticalc.data_io as data_io
from horticalc import paths
from horticalc.data_io import Fertilizer, load_fertilizers, save_fertilizers


def _write_fertilizers_csv(path: Path, rows: list[tuple[str, float]] | None = None) -> None:
    rows = rows or [("Test", 0.1)]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "NR,Düngername,Liquid,Gewicht,N\n"
        + "".join(f"{index},{name},0,1,{value}\n" for index, (name, value) in enumerate(rows, start=1)),
        encoding="utf-8",
    )


def _write_pre_liquid_fertilizers_csv(
    path: Path,
    rows: list[tuple[str, str, float, float]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "Nr.,Düngername,Form,Gewicht,N,Information\n"
        + "".join(
            f"{index},{name},{form},{weight},{value},legacy\n"
            for index, (name, form, weight, value) in enumerate(rows, start=1)
        ),
        encoding="utf-8",
    )


def test_portable_layout_uses_shipped_catalog_and_user_overlay(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    shipped_csv = tmp_path / "data" / "fertilizers.csv"
    _write_fertilizers_csv(shipped_csv, [("Test", 0.1), ("Remove Me", 0.3)])

    layout = paths.ensure_portable_layout(tmp_path)
    assert layout.fertilizers.exists()
    assert not paths.user_fertilizers_path(tmp_path).exists()

    monkeypatch.setattr(paths, "app_root", lambda: tmp_path)

    ferts = load_fertilizers()
    assert "Test" in ferts

    ferts["Extra"] = Fertilizer(name="Extra", liquid=False, weight_factor=1.0, comp={"N": 0.2})
    del ferts["Remove Me"]
    save_fertilizers(ferts)

    overrides_csv = paths.user_fertilizer_overrides_path(tmp_path)
    disabled_txt = paths.user_disabled_fertilizers_path(tmp_path)
    assert overrides_csv.exists()
    assert "Extra" in overrides_csv.read_text(encoding="utf-8")
    with overrides_csv.open("r", encoding="utf-8", newline="") as handle:
        assert next(csv.reader(handle)) == [
            "Düngername",
            "Liquid",
            "Gewicht",
            "N",
            "SolverMaxDosePerL",
        ]
    assert disabled_txt.read_text(encoding="utf-8").strip() == "Remove Me"
    assert "Extra" not in shipped_csv.read_text(encoding="utf-8")

    _write_fertilizers_csv(shipped_csv, [("Test", 0.1), ("Remove Me", 0.3), ("New Shipped", 0.4)])
    reloaded = load_fertilizers()

    assert "Extra" in reloaded
    assert "New Shipped" in reloaded
    assert "Remove Me" not in reloaded


def test_portable_layout_prunes_copied_defaults_and_preserves_user_yaml(tmp_path: Path) -> None:
    shipped_water = tmp_path / "data" / "water_profiles" / "tap.yml"
    shipped_target = tmp_path / "data" / "nutrient_solutions" / "target.yml"
    shipped_recipe = tmp_path / "recipes" / "default.yml"
    for path in (shipped_water, shipped_target, shipped_recipe):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"name: {path.stem}\n", encoding="utf-8")

    copied_water = paths.user_water_profiles_dir(tmp_path) / shipped_water.name
    copied_target = paths.user_nutrient_solutions_dir(tmp_path) / shipped_target.name
    edited_recipe = paths.user_recipes_dir(tmp_path) / shipped_recipe.name
    for source, destination in (
        (shipped_water, copied_water),
        (shipped_target, copied_target),
    ):
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(source.read_bytes())
    edited_recipe.parent.mkdir(parents=True, exist_ok=True)
    edited_recipe.write_text("name: User default\n", encoding="utf-8")

    layout = paths.ensure_portable_layout(tmp_path)

    assert not copied_water.exists()
    assert not copied_target.exists()
    assert edited_recipe.exists()
    assert list(layout.water_profiles.iterdir()) == []
    assert list(layout.nutrient_solutions.iterdir()) == []
    assert paths.default_recipe_path(tmp_path) == edited_recipe


def test_merged_catalog_is_sorted_after_user_overrides(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    shipped_csv = tmp_path / "data" / "fertilizers.csv"
    _write_fertilizers_csv(shipped_csv, [("Zulu", 0.1), ("Bravo", 0.2)])
    _write_fertilizers_csv(paths.user_fertilizer_overrides_path(tmp_path), [("Alpha", 0.3)])
    monkeypatch.setattr(paths, "app_root", lambda: tmp_path)

    assert list(load_fertilizers()) == ["Alpha", "Bravo", "Zulu"]


def test_overlay_save_restores_overrides_when_disabled_write_fails(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    shipped_csv = tmp_path / "data" / "fertilizers.csv"
    _write_fertilizers_csv(shipped_csv, [("Keep", 0.1), ("Remove", 0.2)])
    overrides_path = paths.user_fertilizer_overrides_path(tmp_path)
    _write_fertilizers_csv(overrides_path, [("Previous Custom", 0.4)])
    previous_overrides = overrides_path.read_text(encoding="utf-8")
    monkeypatch.setattr(paths, "app_root", lambda: tmp_path)

    def fail_disabled_write(_names: list[str], _path: Path) -> None:
        raise OSError("disabled write failed")

    monkeypatch.setattr(data_io, "_write_disabled_fertilizers", fail_disabled_write)
    incoming = {
        "Keep": Fertilizer(
            name="Keep",
            liquid=False,
            weight_factor=1.0,
            comp={"N": 0.3},
        )
    }

    with pytest.raises(OSError, match="disabled write failed"):
        save_fertilizers(incoming)

    assert overrides_path.read_text(encoding="utf-8") == previous_overrides
    assert not paths.user_disabled_fertilizers_path(tmp_path).exists()


def test_legacy_user_fertilizers_migrates_custom_rows_and_accepts_shipped_updates(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    shipped_csv = tmp_path / "data" / "fertilizers.csv"
    _write_fertilizers_csv(shipped_csv, [("Existing", 0.2), ("New Shipped", 0.4)])
    _write_fertilizers_csv(paths.user_fertilizers_path(tmp_path), [("Existing", 0.1), ("User Custom", 0.5)])
    monkeypatch.setattr(paths, "app_root", lambda: tmp_path)

    ferts = load_fertilizers()

    assert ferts["Existing"].comp == {"N": 0.2}
    assert ferts["User Custom"].comp == {"N": 0.5}
    assert "New Shipped" in ferts
    assert not paths.user_fertilizers_path(tmp_path).exists()
    assert paths.user_fertilizers_path(tmp_path).with_suffix(".csv.legacy-backup").exists()


def test_pre_liquid_user_fertilizers_migrate_without_blocking_startup(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    shipped_csv = tmp_path / "data" / "fertilizers.csv"
    _write_fertilizers_csv(shipped_csv, [("Existing", 0.2)])
    legacy_path = paths.user_fertilizers_path(tmp_path)
    _write_pre_liquid_fertilizers_csv(
        legacy_path,
        [
            ("Existing", "Pulver", 1.0, 0.1),
            ("Custom Solid", "Pulver", 1.0, 0.3),
            ("Custom Liquid", "Flüssig", 1.25, 0.4),
            ("Custom Blank Form", "", 1.0, 0.5),
        ],
    )
    monkeypatch.setattr(paths, "app_root", lambda: tmp_path)

    fertilizers = load_fertilizers()

    assert fertilizers["Existing"].comp == {"N": 0.2}
    assert fertilizers["Custom Solid"].liquid is False
    assert fertilizers["Custom Blank Form"].liquid is False
    assert fertilizers["Custom Liquid"].liquid is True
    assert fertilizers["Custom Liquid"].weight_factor == pytest.approx(1.25)
    overrides_path = paths.user_fertilizer_overrides_path(tmp_path)
    with overrides_path.open("r", encoding="utf-8", newline="") as handle:
        assert next(csv.reader(handle)) == [
            "Düngername",
            "Liquid",
            "Gewicht",
            "N",
            "SolverMaxDosePerL",
        ]
    assert not legacy_path.exists()
    assert legacy_path.with_suffix(".csv.legacy-backup").exists()


def test_legacy_migration_uses_shipped_replace_aliases_to_avoid_duplicates(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    shipped_csv = tmp_path / "data" / "fertilizers.csv"
    shipped_csv.parent.mkdir(parents=True, exist_ok=True)
    shipped_csv.write_text(
        "NR,Düngername,Liquid,Gewicht,N,Quelle\n"
        '1,New Name,0,1,0.2,"IMPORT ACTION: replace existing row ""Old Name"""\n',
        encoding="utf-8",
    )
    _write_fertilizers_csv(paths.user_fertilizers_path(tmp_path), [("Old Name", 0.1), ("User Custom", 0.5)])
    monkeypatch.setattr(paths, "app_root", lambda: tmp_path)

    ferts = load_fertilizers()

    assert "New Name" in ferts
    assert "Old Name" not in ferts
    assert "User Custom" in ferts
    assert "Old Name" not in paths.user_fertilizer_overrides_path(tmp_path).read_text(encoding="utf-8")


def test_untouched_legacy_nutrient_solution_is_removed_to_use_shipped_default(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    filename = "Legacy.yml"
    shipped = tmp_path / "data" / "nutrient_solutions" / filename
    user = tmp_path / "user" / "nutrient_solutions" / filename
    legacy_bytes = b"name: Legacy\nsource: old\n"
    shipped.parent.mkdir(parents=True)
    user.parent.mkdir(parents=True)
    shipped.write_bytes(b"name: Refreshed\nsource: cited\n")
    user.write_bytes(legacy_bytes.replace(b"\n", b"\r\n"))
    monkeypatch.setattr(
        paths,
        "LEGACY_NUTRIENT_SOLUTION_HASHES",
        {filename: sha256(legacy_bytes).hexdigest()},
    )

    paths._prune_redundant_yaml_overrides(
        shipped.parent,
        user.parent,
        paths.LEGACY_NUTRIENT_SOLUTION_HASHES,
    )

    assert not user.exists()
    assert paths.resolve_layered_yaml_path(filename, user.parent, shipped.parent) == shipped


def test_edited_legacy_nutrient_solution_is_not_overwritten(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    filename = "Legacy.yml"
    shipped = tmp_path / "data" / "nutrient_solutions" / filename
    user = tmp_path / "user" / "nutrient_solutions" / filename
    shipped.parent.mkdir(parents=True)
    user.parent.mkdir(parents=True)
    shipped.write_bytes(b"name: Refreshed\nsource: cited\n")
    user.write_bytes(b"name: User edit\nsource: custom\n")
    monkeypatch.setattr(
        paths,
        "LEGACY_NUTRIENT_SOLUTION_HASHES",
        {filename: sha256(b"name: Legacy\nsource: old\n").hexdigest()},
    )

    paths._prune_redundant_yaml_overrides(
        shipped.parent,
        user.parent,
        paths.LEGACY_NUTRIENT_SOLUTION_HASHES,
    )

    assert user.read_bytes() == b"name: User edit\nsource: custom\n"


@pytest.mark.parametrize("filename", ["../outside.yml", "subdir/../../outside.yml"])
def test_layered_yaml_path_rejects_directory_escape(tmp_path: Path, filename: str) -> None:
    with pytest.raises(ValueError, match="configured directory"):
        paths.resolve_layered_yaml_path(
            filename,
            paths.user_water_profiles_dir(tmp_path),
            paths.shipped_water_profiles_dir(tmp_path),
        )


def test_layered_yaml_path_rejects_absolute_path(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside.yml"

    with pytest.raises(ValueError, match="configured directory"):
        paths.resolve_layered_yaml_path(
            str(outside),
            paths.user_water_profiles_dir(tmp_path),
            paths.shipped_water_profiles_dir(tmp_path),
        )


def test_water_profile_name_resolves_only_layered_profiles(tmp_path: Path) -> None:
    shipped = paths.shipped_water_profiles_dir(tmp_path)
    shipped.mkdir(parents=True)
    expected = shipped / "default.yml"
    expected.write_text("name: Default\nmg_per_l: {}\n", encoding="utf-8")

    assert paths.resolve_water_profile_name("default", tmp_path) == expected
    with pytest.raises(ValueError, match="configured directory"):
        paths.resolve_water_profile_name("../outside", tmp_path)
