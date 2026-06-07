#!/usr/bin/env python3
"""Init script for the Indeed scraper PocketBase instance.

Creates (or updates, idempotently) the three collections that back the
time-series analysis:

  - scrape_runs   : one row per scrape execution (volume time-series)
  - jobs          : the current state of each job offer (1 row / offer)
  - job_snapshots : history of field changes over time (temporal analysis core)

Run PocketBase first (`cd pb && ./pocketbase serve`), then:
    python pb/setup_pocketbase.py
"""

import os
import sys
import time
import json
import subprocess
import httpx
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PB_URL = os.getenv("PB_URL", "http://127.0.0.1:8090").rstrip("/")
PB_SUPERUSER_EMAIL = os.getenv("PB_SUPERUSER_EMAIL", "")
PB_SUPERUSER_PASSWORD = os.getenv("PB_SUPERUSER_PASSWORD", "")
PB_EXECUTABLE = os.getenv("PB_EXECUTABLE", "./pocketbase")

# Access rules: everything is restricted to the superuser (no public access).
_SUPERUSER_ONLY = {
    "listRule": None,
    "viewRule": None,
    "createRule": None,
    "updateRule": None,
    "deleteRule": None,
}

COLLECTIONS = [
    {
        "name": "scrape_runs",
        "type": "base",
        "fields": [
            {"name": "keyword", "type": "text", "required": True},
            {"name": "location", "type": "text"},
            {"name": "jobs_found", "type": "number", "min": 0},
            {"name": "jobs_new", "type": "number", "min": 0},
            {"name": "jobs_updated", "type": "number", "min": 0},
            {"name": "jobs_deactivated", "type": "number", "min": 0},
            {"name": "errors", "type": "number", "min": 0},
            {"name": "duration_seconds", "type": "number", "min": 0},
            {"name": "started_at", "type": "autodate", "onCreate": True, "onUpdate": False},
            {"name": "status", "type": "select", "required": True, "values": ["running", "success", "partial", "failed"], "maxSelect": 1},
            {"name": "error_message", "type": "text"},
        ],
        "indexes": [
            "CREATE INDEX idx_scrape_runs_keyword ON scrape_runs (keyword)",
            "CREATE INDEX idx_scrape_runs_started ON scrape_runs (started_at)",
        ],
        **_SUPERUSER_ONLY,
    },
    {
        "name": "jobs",
        "type": "base",
        "fields": [
            {"name": "title", "type": "text", "required": True},
            {"name": "company", "type": "text", "required": True},
            {"name": "location", "type": "text"},
            {"name": "remote", "type": "select", "values": ["remote", "hybrid", "onsite"], "maxSelect": 1},
            {"name": "salary_min", "type": "number", "min": 0},
            {"name": "salary_max", "type": "number", "min": 0},
            {"name": "salary_currency", "type": "text"},
            {"name": "salary_period", "type": "select", "values": ["year", "month", "week", "day", "hour"], "maxSelect": 1},
            {"name": "contract_type", "type": "select", "values": ["CDI", "CDD", "Freelance", "Stage", "Alternance", "Interim", "Autre"], "maxSelect": 1},
            {"name": "indeed_jk", "type": "text", "required": True},
            {"name": "source_url", "type": "url", "required": True},
            {"name": "description", "type": "editor"},
            {"name": "tags", "type": "json"},
            {"name": "posted_at", "type": "date"},
            {"name": "first_seen_at", "type": "date"},
            {"name": "last_seen_at", "type": "date"},
            {"name": "scraped_at", "type": "autodate", "onCreate": True, "onUpdate": False},
            {"name": "is_active", "type": "bool"},
            {"name": "search_keyword", "type": "text", "required": True},
            {"name": "scrape_run", "type": "relation", "collectionId": "__scrape_runs__", "cascadeDelete": False, "maxSelect": 1},
        ],
        "indexes": [
            "CREATE UNIQUE INDEX idx_jobs_jk ON jobs (indeed_jk)",
            "CREATE INDEX idx_jobs_company ON jobs (company)",
            "CREATE INDEX idx_jobs_posted_at ON jobs (posted_at)",
            "CREATE INDEX idx_jobs_is_active ON jobs (is_active)",
            "CREATE INDEX idx_jobs_search_keyword ON jobs (search_keyword)",
            "CREATE INDEX idx_jobs_contract ON jobs (contract_type)",
        ],
        **_SUPERUSER_ONLY,
    },
    {
        "name": "job_snapshots",
        "type": "base",
        "fields": [
            {"name": "job", "type": "relation", "collectionId": "__jobs__", "cascadeDelete": True, "maxSelect": 1, "required": True},
            {"name": "field_changed", "type": "select", "values": ["title", "salary_min", "salary_max", "location", "remote", "contract_type", "description", "is_active"], "required": True, "maxSelect": 1},
            {"name": "old_value", "type": "text"},
            {"name": "new_value", "type": "text"},
            {"name": "detected_at", "type": "autodate", "onCreate": True, "onUpdate": False},
        ],
        "indexes": [
            "CREATE INDEX idx_snapshots_job ON job_snapshots (job)",
            "CREATE INDEX idx_snapshots_detected_at ON job_snapshots (detected_at)",
            "CREATE INDEX idx_snapshots_field ON job_snapshots (field_changed)",
        ],
        **_SUPERUSER_ONLY,
    },
]


def wait_for_pocketbase(url: str, timeout: int = 30) -> bool:
    print(f"Waiting for PocketBase at {url}...")
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = httpx.get(f"{url}/api/health", timeout=2)
            if r.status_code == 200:
                return True
        except httpx.RequestError:
            pass
        time.sleep(1)
    return False


def create_superuser_via_cli(executable: str, email: str, password: str) -> bool:
    exe = Path(executable)
    if not exe.exists():
        print(f"PocketBase executable not found: {executable}")
        return False

    resolved_exe = str(exe.resolve())
    for cmd in [
        [resolved_exe, "superuser", "create", email, password],
        [resolved_exe, "admin", "create", email, password],
    ]:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            output = (result.stdout + result.stderr).lower()
            if result.returncode == 0:
                print(f"Superuser created: {email}")
                return True
            if "already" in output or "exists" in output or "duplicate" in output:
                print(f"Superuser {email} already exists.")
                return True
            if "unknown command" in output or "no such command" in output:
                continue
            print(f"CLI error: {result.stderr.strip()}")
            return False
        except FileNotFoundError:
            print(f"Failed to execute command: {' '.join(cmd)}")
            return False
        except subprocess.TimeoutExpired:
            print("CLI timeout.")
            return False

    print("No compatible CLI command found.")
    return False


def authenticate(url: str, email: str, password: str, silent: bool = False) -> str | None:
    try:
        r = httpx.post(
            f"{url}/api/collections/_superusers/auth-with-password",
            json={"identity": email, "password": password},
            timeout=10,
        )
        if r.status_code == 200:
            token = r.json()["token"]
            if not silent:
                print("Authentication successful.")
            return token
        if not silent:
            print(f"Authentication failed ({r.status_code}): {r.text}")
        return None
    except httpx.RequestError as e:
        if not silent:
            print(f"Network error during authentication: {e}")
        return None


def get_existing_collections(url: str, token: str) -> dict[str, str]:
    try:
        r = httpx.get(
            f"{url}/api/collections",
            headers={"Authorization": token},
            params={"perPage": 200},
            timeout=10,
        )
        if r.status_code == 200:
            return {c["name"]: c["id"] for c in r.json().get("items", [])}
        return {}
    except httpx.RequestError:
        return {}


def resolve_relation_ids(fields: list, collection_ids: dict) -> list:
    resolved = []
    for field in fields:
        f = field.copy()
        if f.get("type") == "relation":
            placeholder = f.get("collectionId", "")
            if placeholder.startswith("__") and placeholder.endswith("__"):
                cname = placeholder.strip("_")
                real_id = collection_ids.get(cname)
                if real_id:
                    f["collectionId"] = real_id
                else:
                    print(f"Warning: Collection '{cname}' not found for relation.")
                    f.pop("collectionId", None)
        resolved.append(f)
    return resolved


def create_or_update_collection(url: str, token: str, schema: dict, existing: dict[str, str]) -> bool:
    name = schema["name"]
    headers = {"Authorization": token, "Content-Type": "application/json"}
    payload = {
        "name": name,
        "type": schema.get("type", "base"),
        "fields": schema.get("fields", []),
        "indexes": schema.get("indexes", []),
        "listRule": schema.get("listRule"),
        "viewRule": schema.get("viewRule"),
        "createRule": schema.get("createRule"),
        "updateRule": schema.get("updateRule"),
        "deleteRule": schema.get("deleteRule"),
    }
    try:
        if name in existing:
            col_id = existing[name]
            r = httpx.patch(f"{url}/api/collections/{col_id}", headers=headers, content=json.dumps(payload), timeout=15)
            action = "updated"
        else:
            r = httpx.post(f"{url}/api/collections", headers=headers, content=json.dumps(payload), timeout=15)
            action = "created"

        if r.status_code in (200, 201):
            print(f"Collection '{name}' {action}.")
            return True
        print(f"Error for '{name}' - HTTP {r.status_code}: {r.text[:300]}")
        return False
    except httpx.RequestError as e:
        print(f"Network error for '{name}': {e}")
        return False


def main():
    if not PB_SUPERUSER_EMAIL or not PB_SUPERUSER_PASSWORD:
        print("Missing credentials in env configuration.")
        sys.exit(1)
    if len(PB_SUPERUSER_PASSWORD) < 10:
        print("PB_SUPERUSER_PASSWORD must be at least 10 characters.")
        sys.exit(1)

    if not wait_for_pocketbase(PB_URL):
        print("PocketBase is not running.")
        sys.exit(1)

    token = authenticate(PB_URL, PB_SUPERUSER_EMAIL, PB_SUPERUSER_PASSWORD, silent=True)
    if token:
        print("Superuser already configured.")
    else:
        print("Authenticating/creating superuser...")
        if not create_superuser_via_cli(PB_EXECUTABLE, PB_SUPERUSER_EMAIL, PB_SUPERUSER_PASSWORD):
            print("Failed to create superuser.")
            sys.exit(1)
        token = authenticate(PB_URL, PB_SUPERUSER_EMAIL, PB_SUPERUSER_PASSWORD)
        if not token:
            sys.exit(1)

    existing_collections = get_existing_collections(PB_URL, token)
    success_count = 0
    created_ids = {}

    for schema in COLLECTIONS:
        name = schema["name"]
        all_known_ids = {**existing_collections, **created_ids}
        schema_copy = schema.copy()
        schema_copy["fields"] = resolve_relation_ids(schema.get("fields", []), all_known_ids)

        if create_or_update_collection(PB_URL, token, schema_copy, existing_collections):
            success_count += 1
            refreshed = get_existing_collections(PB_URL, token)
            if name in refreshed:
                created_ids[name] = refreshed[name]
                existing_collections = refreshed

    total = len(COLLECTIONS)
    if success_count == total:
        print(f"Setup completed successfully: {success_count}/{total} collections configured.")
        sys.exit(0)
    print(f"Setup partial: {success_count}/{total} collections configured.")
    sys.exit(1)


if __name__ == "__main__":
    main()
