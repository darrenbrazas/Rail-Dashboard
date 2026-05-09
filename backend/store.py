from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED_FILE = ROOT / "data" / "lifecycle.json"
DB_FILE = ROOT / "data" / "lifecycle.db"

REQUIREMENT_STATUSES = {"Verified", "In Review", "Failed", "Not Started"}
CHANGE_PRIORITIES = {"Critical", "High", "Medium", "Low"}
CHANGE_STATUSES = {"Open", "In Analysis", "Approved", "Implemented", "Verified", "Closed"}


def connect(db_path: Path = DB_FILE) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


@contextmanager
def database(db_path: Path = DB_FILE):
    connection = connect(db_path)
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def initialize(db_path: Path = DB_FILE) -> None:
    with database(db_path) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS requirements (
                id TEXT PRIMARY KEY,
                text TEXT NOT NULL,
                config TEXT NOT NULL,
                test TEXT NOT NULL,
                status TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS changes (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                priority TEXT NOT NULL,
                owner TEXT NOT NULL,
                requirement TEXT NOT NULL,
                status TEXT NOT NULL,
                jira_key TEXT,
                jira_url TEXT,
                jira_sync_status TEXT NOT NULL DEFAULT 'Not Synced',
                FOREIGN KEY(requirement) REFERENCES requirements(id)
            );
            """
        )
        migrate_changes_table(connection)
        count = connection.execute("SELECT COUNT(*) FROM requirements").fetchone()[0]
        if count == 0:
            seed_database(connection)


def migrate_changes_table(connection: sqlite3.Connection) -> None:
    columns = {row["name"] for row in connection.execute("PRAGMA table_info(changes)").fetchall()}
    if "jira_key" not in columns:
        connection.execute("ALTER TABLE changes ADD COLUMN jira_key TEXT")
    if "jira_url" not in columns:
        connection.execute("ALTER TABLE changes ADD COLUMN jira_url TEXT")
    if "jira_sync_status" not in columns:
        connection.execute("ALTER TABLE changes ADD COLUMN jira_sync_status TEXT NOT NULL DEFAULT 'Not Synced'")


def seed_database(connection: sqlite3.Connection) -> None:
    with SEED_FILE.open("r", encoding="utf-8") as file:
        seed = json.load(file)

    connection.executemany(
        "INSERT INTO requirements (id, text, config, test, status) VALUES (:id, :text, :config, :test, :status)",
        seed["requirements"],
    )
    connection.executemany(
        """
        INSERT INTO changes (id, title, priority, owner, requirement, status, jira_sync_status)
        VALUES (:id, :title, :priority, :owner, :requirement, :status, 'Not Synced')
        """,
        seed["changes"],
    )


def rows_to_dicts(rows) -> list[dict]:
    return [dict(row) for row in rows]


def list_requirements(db_path: Path = DB_FILE) -> list[dict]:
    with database(db_path) as connection:
        rows = connection.execute("SELECT id, text, config, test, status FROM requirements ORDER BY id").fetchall()
    return rows_to_dicts(rows)


def list_changes(db_path: Path = DB_FILE) -> list[dict]:
    with database(db_path) as connection:
        rows = connection.execute(
            """
            SELECT id, title, priority, owner, requirement, status, jira_key, jira_url, jira_sync_status
            FROM changes
            ORDER BY id
            """
        ).fetchall()
    return rows_to_dicts(rows)


def get_change(change_id: str, db_path: Path = DB_FILE) -> dict | None:
    with database(db_path) as connection:
        row = connection.execute(
            """
            SELECT id, title, priority, owner, requirement, status, jira_key, jira_url, jira_sync_status
            FROM changes
            WHERE id = ?
            """,
            (change_id.upper(),),
        ).fetchone()
    return dict(row) if row else None


def get_requirement(requirement_id: str, db_path: Path = DB_FILE) -> dict | None:
    with database(db_path) as connection:
        row = connection.execute(
            "SELECT id, text, config, test, status FROM requirements WHERE id = ?",
            (requirement_id.upper(),),
        ).fetchone()
    return dict(row) if row else None


def add_requirement(payload: dict, db_path: Path = DB_FILE) -> dict:
    requirement = {
        "id": clean_required(payload, "id").upper(),
        "text": clean_required(payload, "text"),
        "config": clean_required(payload, "config"),
        "test": clean_required(payload, "test").upper(),
        "status": clean_required(payload, "status"),
    }
    if requirement["status"] not in REQUIREMENT_STATUSES:
        raise ValueError(f"status must be one of: {', '.join(sorted(REQUIREMENT_STATUSES))}")

    with database(db_path) as connection:
        connection.execute(
            "INSERT INTO requirements (id, text, config, test, status) VALUES (:id, :text, :config, :test, :status)",
            requirement,
        )
    return requirement


def add_change(payload: dict, db_path: Path = DB_FILE) -> dict:
    change = {
        "id": clean_required(payload, "id").upper(),
        "title": clean_required(payload, "title"),
        "priority": clean_required(payload, "priority"),
        "owner": clean_required(payload, "owner"),
        "requirement": clean_required(payload, "requirement").upper(),
        "status": clean_required(payload, "status"),
    }
    if change["priority"] not in CHANGE_PRIORITIES:
        raise ValueError(f"priority must be one of: {', '.join(sorted(CHANGE_PRIORITIES))}")
    if change["status"] not in CHANGE_STATUSES:
        raise ValueError(f"status must be one of: {', '.join(sorted(CHANGE_STATUSES))}")

    with database(db_path) as connection:
        exists = connection.execute(
            "SELECT 1 FROM requirements WHERE id = ?",
            (change["requirement"],),
        ).fetchone()
        if not exists:
            raise ValueError("linked requirement does not exist")
        connection.execute(
            """
            INSERT INTO changes (id, title, priority, owner, requirement, status, jira_sync_status)
            VALUES (:id, :title, :priority, :owner, :requirement, :status, 'Not Synced')
            """,
            change,
        )
    return change


def update_change_jira(change_id: str, jira_key: str, jira_url: str, sync_status: str, db_path: Path = DB_FILE) -> dict:
    with database(db_path) as connection:
        connection.execute(
            """
            UPDATE changes
            SET jira_key = ?, jira_url = ?, jira_sync_status = ?
            WHERE id = ?
            """,
            (jira_key, jira_url, sync_status, change_id.upper()),
        )
    change = get_change(change_id, db_path)
    if not change:
        raise ValueError("change request not found")
    return change


def clean_required(payload: dict, field: str) -> str:
    value = str(payload.get(field, "")).strip()
    if not value:
        raise ValueError(f"{field} is required")
    return value
