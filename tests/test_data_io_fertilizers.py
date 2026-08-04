import csv
from pathlib import Path

import pytest

import horticalc.data_io as data_io
from horticalc import paths
from horticalc.data_io import Fertilizer, load_fertilizers, save_fertilizers


def test_load_fertilizers_ignores_number_field(tmp_path: Path) -> None:
    csv_path = tmp_path / "fertilizers.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Nr.", "Düngername", "Liquid", "Gewicht", "NH4", "NO3"])
        writer.writerow(["12", "Test Dünger", "0", "1.5", "0.12", "0"])

    fertilizers = load_fertilizers(csv_path)
    fert = fertilizers["Test Dünger"]

    assert fert.liquid is False
    assert fert.comp == {"NH4": 0.12}


def test_load_fertilizers_accepts_ascii_name_header(tmp_path: Path) -> None:
    csv_path = tmp_path / "fertilizers.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["NR", "Duengername", "Liquid", "Gewicht", "NO3"])
        writer.writerow(["1", "Ascii Header", "1", "1", "0.11"])

    fertilizers = load_fertilizers(csv_path)

    assert fertilizers["Ascii Header"].liquid is True
    assert fertilizers["Ascii Header"].comp == {"NO3": 0.11}


def test_save_fertilizers_removes_legacy_number_column(tmp_path: Path) -> None:
    csv_path = tmp_path / "fertilizers.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Nr.", "Düngername", "Liquid", "Gewicht", "NH4"])

    fertilizers = {
        "Test Dünger": Fertilizer(
            name="Test Dünger",
            liquid=False,
            weight_factor=1.5,
            comp={"NH4": 0.12},
        )
    }
    save_fertilizers(fertilizers, csv_path)

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert reader.fieldnames == [
        "Düngername",
        "Liquid",
        "Gewicht",
        "NH4",
        "SolverMaxDosePerL",
    ]
    assert rows[0]["Liquid"] == "0"
    assert rows[0]["NH4"] == "0.12"


def test_solver_max_dose_csv_roundtrip_is_not_composition(tmp_path: Path) -> None:
    csv_path = tmp_path / "fertilizers.csv"
    csv_path.write_text(
        "Düngername,Liquid,Gewicht,NO3,SolverMaxDosePerL\nLimited,0,1,0.1,0.25\n",
        encoding="utf-8",
    )

    loaded = load_fertilizers(csv_path)
    assert loaded["Limited"].comp == {"NO3": 0.1}
    assert loaded["Limited"].solver_max_dose_per_l == 0.25

    save_fertilizers(loaded, csv_path)
    reloaded = load_fertilizers(csv_path)
    assert reloaded["Limited"].solver_max_dose_per_l == 0.25
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        assert list(csv.DictReader(handle).fieldnames or [])[-1] == "SolverMaxDosePerL"


@pytest.mark.parametrize("value", ["-0.1", "nan", "inf"])
def test_load_fertilizers_rejects_invalid_solver_max(tmp_path: Path, value: str) -> None:
    csv_path = tmp_path / "fertilizers.csv"
    csv_path.write_text(
        f"Düngername,Liquid,Gewicht,SolverMaxDosePerL\nInvalid,0,1,{value}\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="SolverMaxDosePerL"):
        load_fertilizers(csv_path)


def test_load_fertilizers_sorts_factory_and_user_names_together(tmp_path: Path) -> None:
    csv_path = tmp_path / "fertilizers.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Düngername", "Liquid", "Gewicht", "NO3"])
        writer.writerow(["zeta", "0", "1", "0.1"])
        writer.writerow(["Ähre", "0", "1", "0.2"])
        writer.writerow(["Alpha", "0", "1", "0.3"])

    assert list(load_fertilizers(csv_path)) == ["Alpha", "zeta", "Ähre"]


def test_load_fertilizers_rejects_non_boolean_liquid_value(tmp_path: Path) -> None:
    csv_path = tmp_path / "fertilizers.csv"
    csv_path.write_text(
        "Düngername,Liquid,Gewicht,NO3\nInvalid,Flüssig,1,0.1\n",
        encoding="utf-8",
    )

    try:
        load_fertilizers(csv_path)
    except ValueError as error:
        assert "Liquid must be 0 or 1" in str(error)
    else:
        raise AssertionError("textual Liquid values must be rejected")


def test_load_fertilizers_requires_liquid_column(tmp_path: Path) -> None:
    csv_path = tmp_path / "fertilizers.csv"
    csv_path.write_text(
        "Düngername,Gewicht,NO3\nInvalid,1,0.1\n",
        encoding="utf-8",
    )

    try:
        load_fertilizers(csv_path)
    except ValueError as error:
        assert "requires Liquid" in str(error)
    else:
        raise AssertionError("Liquid column must be required")


@pytest.mark.parametrize(
    "row",
    [
        "Invalid,0,inf,0.1\n",
        "Invalid,0,1,nan\n",
    ],
)
def test_load_fertilizers_rejects_non_finite_numbers(tmp_path: Path, row: str) -> None:
    csv_path = tmp_path / "fertilizers.csv"
    csv_path.write_text(
        "Düngername,Liquid,Gewicht,NO3\n" + row,
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="finite"):
        load_fertilizers(csv_path)


@pytest.mark.parametrize("weight", ["0", "-1"])
def test_load_fertilizers_rejects_non_positive_weight(tmp_path: Path, weight: str) -> None:
    csv_path = tmp_path / "fertilizers.csv"
    csv_path.write_text(
        f"Düngername,Liquid,Gewicht,NO3\nInvalid,0,{weight},0.1\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="greater than zero"):
        load_fertilizers(csv_path)


def test_load_fertilizers_rejects_normalized_duplicate_names(tmp_path: Path) -> None:
    csv_path = tmp_path / "fertilizers.csv"
    csv_path.write_text(
        "Düngername,Liquid,Gewicht,NO3\nTest,0,1,0.1\n test ,0,1,0.2\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="duplicate fertilizer name"):
        load_fertilizers(csv_path)


def test_save_fertilizers_rejects_non_finite_numbers(tmp_path: Path) -> None:
    csv_path = tmp_path / "fertilizers.csv"
    fertilizers = {
        "Invalid": Fertilizer(
            name="Invalid",
            liquid=False,
            weight_factor=1.0,
            comp={"NO3": float("inf")},
        )
    }

    with pytest.raises(ValueError, match="finite"):
        save_fertilizers(fertilizers, csv_path)

    assert not csv_path.exists()


def test_save_fertilizers_rejects_zero_weight(tmp_path: Path) -> None:
    csv_path = tmp_path / "fertilizers.csv"
    fertilizers = {
        "Invalid": Fertilizer(
            name="Invalid",
            liquid=False,
            weight_factor=0,
            comp={"NO3": 0.1},
        )
    }

    with pytest.raises(ValueError, match="greater than zero"):
        save_fertilizers(fertilizers, csv_path)

    assert not csv_path.exists()


def test_overlay_save_validates_all_incoming_fertilizers(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    shipped_path = tmp_path / "data" / "fertilizers.csv"
    shipped_path.parent.mkdir(parents=True)
    shipped_path.write_text(
        "Düngername,Liquid,Gewicht,NO3\nExisting,0,1,0.1\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(paths, "app_root", lambda: tmp_path)
    incoming = {
        "Existing": Fertilizer(
            name="Existing",
            liquid=False,
            weight_factor=float("nan"),
            comp={"NO3": 0.1},
        )
    }

    with pytest.raises(ValueError, match="finite"):
        save_fertilizers(incoming)

    assert not paths.user_fertilizer_overrides_path(tmp_path).exists()


def test_atomic_fertilizer_save_preserves_existing_file_on_replace_failure(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    csv_path = tmp_path / "fertilizers.csv"
    original = "Düngername,Liquid,Gewicht,NO3\nOriginal,0,1,0.1\n"
    csv_path.write_text(original, encoding="utf-8")
    fertilizers = {
        "Updated": Fertilizer(
            name="Updated",
            liquid=False,
            weight_factor=1.0,
            comp={"NO3": 0.2},
        )
    }

    def fail_replace(_source: Path, _destination: Path) -> None:
        raise OSError("replace failed")

    monkeypatch.setattr(data_io.os, "replace", fail_replace)

    with pytest.raises(OSError, match="replace failed"):
        save_fertilizers(fertilizers, csv_path)

    assert csv_path.read_text(encoding="utf-8") == original
    assert list(tmp_path.glob(".fertilizers.csv.tmp-*")) == []
