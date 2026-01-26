from __future__ import annotations

from pathlib import Path

import pytest

from horticalc.data_io import Fertilizer, load_fertilizers, save_fertilizers
from horticalc import paths


def _write_fertilizers_csv(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "NR,Düngername,Form,Gewicht,N\n"
        "1,Test,fest,1,0.1\n",
        encoding="utf-8",
    )


def test_portable_layout_copies_defaults_and_uses_user(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    shipped_csv = tmp_path / "data" / "fertilizers.csv"
    _write_fertilizers_csv(shipped_csv)

    layout = paths.ensure_portable_layout(tmp_path)
    assert layout.fertilizers.exists()

    monkeypatch.setattr(paths, "app_root", lambda: tmp_path)

    ferts = load_fertilizers()
    assert "Test" in ferts

    ferts["Extra"] = Fertilizer(name="Extra", form="fest", weight_factor=1.0, comp={"N": 0.2})
    save_fertilizers(ferts)

    user_csv = paths.user_fertilizers_path(tmp_path)
    assert user_csv.exists()
    assert "Extra" in user_csv.read_text(encoding="utf-8")
    assert "Extra" not in shipped_csv.read_text(encoding="utf-8")
