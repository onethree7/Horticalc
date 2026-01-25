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
api_app.RecipeRequest.model_rebuild(_types_namespace=api_app.__dict__)
api_app.CalculationResponse.model_rebuild(_types_namespace=api_app.__dict__)


class TestWaterProfileSchema(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(api_app.app)

    def test_water_profile_schema_endpoint_returns_labels(self) -> None:
        response = self.client.get("/schema/water-profile")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIsInstance(payload, list)
        nh4_entry = next((item for item in payload if item.get("key") == "NH4"), None)
        self.assertIsNotNone(nh4_entry)
        self.assertEqual(nh4_entry.get("label"), "Ammonium in NH4")


if __name__ == "__main__":
    unittest.main()
