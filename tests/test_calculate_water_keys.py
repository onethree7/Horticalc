import tempfile
import unittest
from pathlib import Path

import yaml
from fastapi.testclient import TestClient

import api.app as api_app

class TestCalculateWaterKeys(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(api_app.app)

    def test_invalid_water_key_in_payload_returns_400(self) -> None:
        response = self.client.post(
            "/calculate",
            json={
                "liters": 10,
                "fertilizers": [],
                "water_mg_l": {"INVALID": 1},
                "osmosis_percent": 0,
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Invalid water key: INVALID")

    def test_invalid_water_key_in_profile_returns_400(self) -> None:
        original_dir = api_app.WATER_PROFILES_DIR
        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_path = Path(tmp_dir)
                api_app.WATER_PROFILES_DIR = tmp_path
                profile_path = tmp_path / "broken.yml"
                profile_path.write_text(
                    yaml.safe_dump(
                        {
                            "name": "broken",
                            "mg_per_l": {"INVALID": 1},
                            "osmosis_percent": 0,
                        }
                    )
                )

                response = self.client.post(
                    "/calculate",
                    json={
                        "liters": 10,
                        "fertilizers": [],
                        "water_profile_name": "broken.yml",
                    },
                )
        finally:
            api_app.WATER_PROFILES_DIR = original_dir

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Invalid water key: INVALID")

    def test_water_profile_name_without_suffix_is_accepted(self) -> None:
        original_dir = api_app.WATER_PROFILES_DIR
        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_path = Path(tmp_dir)
                api_app.WATER_PROFILES_DIR = tmp_path
                profile_path = tmp_path / "simple.yml"
                profile_path.write_text(
                    yaml.safe_dump(
                        {
                            "name": "simple",
                            "mg_per_l": {"Ca": 5},
                            "osmosis_percent": 0,
                        }
                    )
                )

                response = self.client.post(
                    "/calculate",
                    json={
                        "liters": 10,
                        "fertilizers": [],
                        "water_profile_name": "simple",
                    },
                )
        finally:
            api_app.WATER_PROFILES_DIR = original_dir

        self.assertEqual(response.status_code, 200)

if __name__ == "__main__":
    unittest.main()
