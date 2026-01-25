import sys
import unittest
from pathlib import Path

import importlib.util

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "src"))

spec = importlib.util.spec_from_file_location("api_app", ROOT / "api" / "app.py")
api_app = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(api_app)
api_app.SolveRequest.model_rebuild(_types_namespace=api_app.__dict__)
api_app.SolveResponse.model_rebuild(_types_namespace=api_app.__dict__)


class TestSolveTargetKeys(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(api_app.app)

    def test_invalid_target_key_returns_400(self) -> None:
        response = self.client.post(
            "/solve",
            json={
                "liters": 10,
                "targets": {"INVALID": 1},
                "fertilizers_allowed": [],
                "fixed_grams": {},
                "urea_as_nh4": False,
                "phosphate_species": "H2PO4",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Invalid target key: INVALID")


if __name__ == "__main__":
    unittest.main()
