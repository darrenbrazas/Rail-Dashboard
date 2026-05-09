import unittest
from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from jira_client import JiraClient


class JiraClientTests(unittest.TestCase):
    def test_dry_run_generates_predictable_issue_key_and_url(self):
        client = JiraClient(
            {
                "base_url": "https://example.atlassian.net",
                "email": "",
                "api_token": "",
                "project_key": "RAIL",
                "issue_type": "Task",
                "dry_run": True,
            }
        )

        result = client.create_issue(
            {
                "id": "CHG-104",
                "title": "Update braking threshold",
                "priority": "High",
                "owner": "Systems Design",
                "requirement": "SW-REQ-008",
                "status": "In Analysis",
            },
            None,
        )

        self.assertEqual(result.key, "RAIL-104")
        self.assertEqual(result.url, "https://example.atlassian.net/browse/RAIL-104")
        self.assertTrue(result.dry_run)

    def test_live_mode_requires_credentials(self):
        client = JiraClient(
            {
                "base_url": "",
                "email": "",
                "api_token": "",
                "project_key": "RAIL",
                "issue_type": "Task",
                "dry_run": False,
            }
        )

        with self.assertRaises(ValueError):
            client.create_issue(
                {
                    "id": "CHG-104",
                    "title": "Update braking threshold",
                    "priority": "High",
                    "owner": "Systems Design",
                    "requirement": "SW-REQ-008",
                    "status": "In Analysis",
                },
                None,
            )


if __name__ == "__main__":
    unittest.main()
