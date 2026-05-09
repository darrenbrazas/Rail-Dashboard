import unittest
from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

import store


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.db_path = ROOT / "data" / "test_store.db"
        if self.db_path.exists():
            self.db_path.unlink()
        store.initialize(self.db_path)

    def tearDown(self):
        if self.db_path.exists():
            self.db_path.unlink()

    def test_add_requirement_persists_record(self):
        created = store.add_requirement(
            {
                "id": "sw-req-099",
                "text": "Door control software shall report degraded mode within two seconds.",
                "config": "Door-Control-Module v1.4",
                "test": "fit-door-099",
                "status": "In Review",
            },
            self.db_path,
        )

        ids = {item["id"] for item in store.list_requirements(self.db_path)}
        self.assertEqual(created["id"], "SW-REQ-099")
        self.assertIn("SW-REQ-099", ids)

    def test_add_change_rejects_missing_requirement(self):
        with self.assertRaises(ValueError):
            store.add_change(
                {
                    "id": "CHG-999",
                    "title": "Invalid linked requirement",
                    "priority": "High",
                    "owner": "Systems",
                    "requirement": "NO-REQ-000",
                    "status": "Open",
                },
                self.db_path,
            )

    def test_add_change_links_to_requirement(self):
        created = store.add_change(
            {
                "id": "CHG-151",
                "title": "Update release audit evidence",
                "priority": "Medium",
                "owner": "Configuration Management",
                "requirement": "DOC-REQ-017",
                "status": "Approved",
            },
            self.db_path,
        )

        self.assertEqual(created["requirement"], "DOC-REQ-017")
        self.assertIn("CHG-151", {item["id"] for item in store.list_changes(self.db_path)})

    def test_update_change_jira_stores_issue_link(self):
        updated = store.update_change_jira(
            "CHG-104",
            "RAIL-104",
            "https://example.atlassian.net/browse/RAIL-104",
            "Dry Run",
            self.db_path,
        )

        self.assertEqual(updated["jira_key"], "RAIL-104")
        self.assertEqual(updated["jira_sync_status"], "Dry Run")


if __name__ == "__main__":
    unittest.main()
