import importlib.util
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT / "src"))

from horticalc import packaging
from horticalc.core import run_recipe


def test_packaging_spec_exists() -> None:
    spec_path = packaging.get_spec_path()
    assert spec_path.exists()


def test_main_module_imports_when_package_missing() -> None:
    main_path = Path(packaging.__file__).parent / "__main__.py"
    spec = importlib.util.spec_from_file_location("horticalc__main__standalone", main_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.run_recipe is run_recipe
