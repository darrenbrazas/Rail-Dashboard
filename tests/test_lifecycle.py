import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class LifecycleDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with (ROOT / "data" / "lifecycle.json").open("r", encoding="utf-8") as file:
            cls.data = json.load(file)

    def test_every_requirement_links_to_config_and_test(self):
        for requirement in self.data["requirements"]:
            with self.subTest(requirement=requirement["id"]):
                self.assertTrue(requirement["config"])
                self.assertTrue(requirement["test"])

    def test_change_requests_link_to_existing_requirements(self):
        requirement_ids = {item["id"] for item in self.data["requirements"]}
        for change in self.data["changes"]:
            with self.subTest(change=change["id"]):
                self.assertIn(change["requirement"], requirement_ids)

    def test_kpis_are_percentages(self):
        for label, value in self.data["kpis"]:
            with self.subTest(kpi=label):
                self.assertGreaterEqual(value, 0)
                self.assertLessEqual(value, 100)


if __name__ == "__main__":
    unittest.main()
