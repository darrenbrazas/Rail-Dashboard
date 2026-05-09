from __future__ import annotations

import base64
import json
import urllib.error
import urllib.request
from dataclasses import dataclass


@dataclass
class JiraResult:
    key: str
    url: str
    dry_run: bool


class JiraClient:
    def __init__(self, settings: dict):
        self.settings = settings

    def create_issue(self, change: dict, requirement: dict | None) -> JiraResult:
        if self.settings["dry_run"]:
            key = f"{self.settings['project_key']}-{change['id'].split('-')[-1]}"
            return JiraResult(
                key=key,
                url=f"{self.settings['base_url'] or 'https://example.atlassian.net'}/browse/{key}",
                dry_run=True,
            )

        self._validate_settings()
        payload = {
            "fields": {
                "project": {"key": self.settings["project_key"]},
                "summary": f"{change['id']}: {change['title']}",
                "issuetype": {"name": self.settings["issue_type"]},
                "description": self._description(change, requirement),
                "labels": ["rail-lifecycle", "configuration-management"],
            }
        }
        request = urllib.request.Request(
            f"{self.settings['base_url']}/rest/api/3/issue",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Basic {self._basic_auth()}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            details = error.read().decode("utf-8")
            raise ValueError(f"Jira rejected the issue create request: {details}") from error

        key = body["key"]
        return JiraResult(key=key, url=f"{self.settings['base_url']}/browse/{key}", dry_run=False)

    def _validate_settings(self) -> None:
        missing = [
            name
            for name in ("base_url", "email", "api_token", "project_key", "issue_type")
            if not self.settings.get(name)
        ]
        if missing:
            raise ValueError(f"missing Jira settings: {', '.join(missing)}")

    def _basic_auth(self) -> str:
        token = f"{self.settings['email']}:{self.settings['api_token']}".encode("utf-8")
        return base64.b64encode(token).decode("ascii")

    def _description(self, change: dict, requirement: dict | None) -> dict:
        requirement_text = "No linked requirement found."
        if requirement:
            requirement_text = (
                f"{requirement['id']} - {requirement['text']}\n"
                f"Config item: {requirement['config']}\n"
                f"Linked test: {requirement['test']}\n"
                f"Verification status: {requirement['status']}"
            )
        text = (
            f"Owner: {change['owner']}\n"
            f"Priority: {change['priority']}\n"
            f"Local workflow status: {change['status']}\n\n"
            f"Linked requirement:\n{requirement_text}"
        )
        return {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": text}],
                }
            ],
        }
