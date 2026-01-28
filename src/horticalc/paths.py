from __future__ import annotations

import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from shutil import copyfile


PORTABLE_WRITE_ERROR = (
    "Extract to a writable folder (e.g. Desktop/Downloads). "
    "Do not run from Program Files."
)


def repo_root() -> Path:
    # this file lives in .../src/horticalc/paths.py
    return Path(__file__).resolve().parents[2]


def app_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return repo_root()


def user_dir(root: Path | None = None) -> Path:
    base = root or app_root()
    return base / "user"


def logs_dir(root: Path | None = None) -> Path:
    base = root or app_root()
    return base / "logs"


def shipped_data_dir(root: Path | None = None) -> Path:
    base = root or app_root()
    return base / "data"


def shipped_recipes_dir(root: Path | None = None) -> Path:
    base = root or app_root()
    return base / "recipes"


def user_fertilizers_path(root: Path | None = None) -> Path:
    return user_dir(root) / "fertilizers.csv"


def user_water_profiles_dir(root: Path | None = None) -> Path:
    return user_dir(root) / "water_profiles"


def user_nutrient_solutions_dir(root: Path | None = None) -> Path:
    return user_dir(root) / "nutrient_solutions"


def user_recipes_dir(root: Path | None = None) -> Path:
    return user_dir(root) / "recipes"


def default_recipe_path(root: Path | None = None) -> Path:
    return user_recipes_dir(root) / "default.yml"


def shipped_fertilizers_path(root: Path | None = None) -> Path:
    return shipped_data_dir(root) / "fertilizers.csv"


def shipped_water_profiles_dir(root: Path | None = None) -> Path:
    return shipped_data_dir(root) / "water_profiles"


def shipped_nutrient_solutions_dir(root: Path | None = None) -> Path:
    return shipped_data_dir(root) / "nutrient_solutions"


def _atomic_copy(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        delete=False,
        dir=destination.parent,
        prefix=f".{destination.name}.tmp-",
    ) as temp_file:
        temp_path = Path(temp_file.name)
    try:
        copyfile(source, temp_path)
        os.replace(temp_path, destination)
    finally:
        try:
            temp_path.unlink(missing_ok=True)
        except OSError:
            pass


def _copy_if_missing(source: Path, destination: Path) -> None:
    if destination.exists():
        return
    _atomic_copy(source, destination)


def _ensure_writable_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    test_file = path / ".write_test"
    test_file.write_text("ok", encoding="utf-8")
    test_file.unlink(missing_ok=True)


@dataclass(frozen=True)
class PortableLayout:
    root: Path
    user: Path
    logs: Path
    fertilizers: Path
    water_profiles: Path
    nutrient_solutions: Path
    recipes: Path


def ensure_portable_layout(root: Path | None = None) -> PortableLayout:
    base = root or app_root()
    logs = logs_dir(base)
    user = user_dir(base)
    try:
        _ensure_writable_dir(logs)
        _ensure_writable_dir(user)
    except OSError as exc:
        raise RuntimeError(PORTABLE_WRITE_ERROR) from exc

    fertilizers_path = user_fertilizers_path(base)
    water_profiles = user_water_profiles_dir(base)
    nutrient_solutions = user_nutrient_solutions_dir(base)
    recipes = user_recipes_dir(base)
    water_profiles.mkdir(parents=True, exist_ok=True)
    nutrient_solutions.mkdir(parents=True, exist_ok=True)
    recipes.mkdir(parents=True, exist_ok=True)

    shipped_fertilizers = shipped_fertilizers_path(base)
    if shipped_fertilizers.exists():
        _copy_if_missing(shipped_fertilizers, fertilizers_path)

    shipped_water_profiles = shipped_water_profiles_dir(base)
    if shipped_water_profiles.exists():
        for source in sorted(shipped_water_profiles.glob("*.yml")):
            _copy_if_missing(source, water_profiles / source.name)

    shipped_nutrient_solutions = shipped_nutrient_solutions_dir(base)
    if shipped_nutrient_solutions.exists():
        for source in sorted(shipped_nutrient_solutions.glob("*.yml")):
            _copy_if_missing(source, nutrient_solutions / source.name)

    shipped_recipes = shipped_recipes_dir(base)
    if shipped_recipes.exists():
        for source in sorted(shipped_recipes.glob("*.yml")):
            _copy_if_missing(source, recipes / source.name)

    return PortableLayout(
        root=base,
        user=user,
        logs=logs,
        fertilizers=fertilizers_path,
        water_profiles=water_profiles,
        nutrient_solutions=nutrient_solutions,
        recipes=recipes,
    )
