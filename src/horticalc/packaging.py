from __future__ import annotations

from pathlib import Path
import subprocess
import sys


def get_spec_path() -> Path:
    project_root = Path(__file__).resolve().parents[2]
    return project_root / "scripts" / "packaging" / "horticalc.spec"


def build_binary() -> None:
    spec_path = get_spec_path()
    if not spec_path.exists():
        raise FileNotFoundError(f"PyInstaller spec not found: {spec_path}")

    subprocess.run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--clean",
            "--noconfirm",
            str(spec_path),
        ],
        check=True,
    )


def main() -> None:
    build_binary()


if __name__ == "__main__":
    main()
