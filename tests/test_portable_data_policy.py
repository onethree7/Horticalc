from __future__ import annotations

from pathlib import Path

import pytest

from horticalc.data_io import Fertilizer, load_fertilizers, save_fertilizers
from horticalc import paths

def _write_fertilizers_csv(path: Path, rows: list[tuple[str, float]] | None = None) -> None:
    rows = rows or [("Test", 0.1)]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "NR,Düngername,Liquid,Gewicht,N\n"
        + "".join(f"{index},{name},0,1,{value}\n" for index, (name, value) in enumerate(rows, start=1)),
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
    assert disabled_txt.read_text(encoding="utf-8").strip() == "Remove Me"
    assert "Extra" not in shipped_csv.read_text(encoding="utf-8")

    _write_fertilizers_csv(shipped_csv, [("Test", 0.1), ("Remove Me", 0.3), ("New Shipped", 0.4)])
    reloaded = load_fertilizers()

    assert "Extra" in reloaded
    assert "New Shipped" in reloaded
    assert "Remove Me" not in reloaded


def test_merged_catalog_is_sorted_after_user_overrides(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    shipped_csv = tmp_path / "data" / "fertilizers.csv"
    _write_fertilizers_csv(shipped_csv, [("Zulu", 0.1), ("Bravo", 0.2)])
    _write_fertilizers_csv(paths.user_fertilizer_overrides_path(tmp_path), [("Alpha", 0.3)])
    monkeypatch.setattr(paths, "app_root", lambda: tmp_path)

    assert list(load_fertilizers()) == ["Alpha", "Bravo", "Zulu"]

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
