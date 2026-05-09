from __future__ import annotations

import json
import sys
import csv
import io
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

import store
import config
from jira_client import JiraClient

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "lifecycle.json"
SIMULATION_FILE = ROOT / "generated" / "simulation-results.json"


def read_json(path: Path, fallback):
    if not path.exists():
        return fallback
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def build_metrics(data: dict) -> dict:
    requirements = data["requirements"]
    test_runs = data["testRuns"]
    baselines = data["baselines"]

    verified = sum(1 for item in requirements if item["status"] == "Verified")
    passed = sum(run["passed"] for run in test_runs)
    failed = sum(run["failed"] for run in test_runs)
    total = passed + failed

    return {
        "requirementsVerified": round((verified / len(requirements)) * 100),
        "openChanges": len(data["changes"]),
        "buildHealth": round((passed / total) * 100) if total else 0,
        "procurementRisk": sum(1 for item in baselines if item["risk"] == "bad"),
    }


class RailLifecycleHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/lifecycle":
            return self.send_json(self.lifecycle_payload())
        if path == "/api/health":
            return self.send_json({"status": "ok", "service": "rail-lifecycle-api"})
        if path == "/api/integrations":
            return self.send_json({"jira": self.jira_status()})
        if path == "/api/export/traceability.csv":
            return self.send_traceability_csv()
        return super().do_GET()

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            payload = self.read_body_json()
            if path == "/api/requirements":
                created = store.add_requirement(payload)
                return self.send_json(created, status=201)
            if path == "/api/changes":
                created = store.add_change(payload)
                return self.send_json(created, status=201)
            if path.startswith("/api/changes/") and path.endswith("/sync-jira"):
                change_id = path.split("/")[3]
                synced = self.sync_change_to_jira(change_id)
                return self.send_json(synced)
            return self.send_error_json(404, "endpoint not found")
        except ValueError as error:
            return self.send_error_json(400, str(error))
        except Exception as error:
            return self.send_error_json(500, f"server error: {error}")

    def lifecycle_payload(self) -> dict:
        data = read_json(DATA_FILE, {})
        data["requirements"] = store.list_requirements()
        data["changes"] = store.list_changes()
        simulation = read_json(SIMULATION_FILE, {"scenarios": [], "summary": "Simulation has not been generated yet."})
        return {
            **data,
            "metrics": build_metrics(data),
            "simulation": simulation,
        }

    def read_body_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8")
        if not raw:
            return {}
        return json.loads(raw)

    def send_json(self, payload: dict, status: int = 200):
        encoded = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def send_error_json(self, status: int, message: str):
        return self.send_json({"error": message}, status=status)

    def send_traceability_csv(self):
        data = self.lifecycle_payload()
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["Requirement ID", "Requirement", "Configuration Item", "Linked Test", "Status"])
        for requirement in data["requirements"]:
            writer.writerow(
                [
                    requirement["id"],
                    requirement["text"],
                    requirement["config"],
                    requirement["test"],
                    requirement["status"],
                ]
            )
        encoded = buffer.getvalue().encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/csv; charset=utf-8")
        self.send_header("Content-Disposition", "attachment; filename=traceability-matrix.csv")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def jira_status(self) -> dict:
        settings = config.jira_settings()
        return {
            "configured": bool(settings["base_url"] and settings["email"] and settings["api_token"]),
            "dryRun": settings["dry_run"],
            "baseUrl": settings["base_url"],
            "projectKey": settings["project_key"],
            "issueType": settings["issue_type"],
        }

    def sync_change_to_jira(self, change_id: str) -> dict:
        change = store.get_change(change_id)
        if not change:
            raise ValueError("change request not found")
        requirement = store.get_requirement(change["requirement"])
        result = JiraClient(config.jira_settings()).create_issue(change, requirement)
        status = "Dry Run" if result.dry_run else "Synced"
        return store.update_change_jira(change_id, result.key, result.url, status)


def main():
    store.initialize()
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    server = ThreadingHTTPServer(("127.0.0.1", port), RailLifecycleHandler)
    print(f"Rail Lifecycle API running at http://127.0.0.1:{port}")
    print(f"Dashboard: http://127.0.0.1:{port}/index.html")
    server.serve_forever()


if __name__ == "__main__":
    main()
