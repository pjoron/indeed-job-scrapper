"""Upsert scraped jobs into PocketBase and record temporal diffs."""

from __future__ import annotations

import time
from datetime import date, datetime, timezone
from typing import Any, Optional

from loguru import logger

from config import Search
from scraper.models import JobDTO
from .client import PocketBaseClient

# Fields compared between runs; a change writes a job_snapshots row.
_TRACKED_FIELDS = [
    "title", "salary_min", "salary_max", "location",
    "remote", "contract_type", "description", "is_active",
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.000Z")


def _date_iso(d: Optional[date]) -> Optional[str]:
    if d is None:
        return None
    return d.strftime("%Y-%m-%d 00:00:00.000Z")


def _dto_to_record(job: JobDTO) -> dict[str, Any]:
    return {
        "title": job.title,
        "company": job.company,
        "location": job.location,
        "remote": job.remote,
        "salary_min": job.salary_min,
        "salary_max": job.salary_max,
        "salary_currency": job.salary_currency,
        "salary_period": job.salary_period,
        "contract_type": job.contract_type,
        "indeed_jk": job.indeed_jk,
        "source_url": job.source_url,
        "description": job.description,
        "tags": job.tags,
        "posted_at": _date_iso(job.posted_at),
    }


def _norm(value: Any) -> str:
    """Normalise a value for comparison/snapshot storage."""
    if value is None or value == "":
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _diff(existing: dict[str, Any], incoming: dict[str, Any]) -> list[tuple[str, str, str]]:
    changes = []
    for f in _TRACKED_FIELDS:
        if f == "is_active":
            continue  # is_active is handled by the (de)activation logic
        old, new = _norm(existing.get(f)), _norm(incoming.get(f))
        if old != new:
            changes.append((f, old, new))
    return changes


def store_jobs(client: PocketBaseClient, search: Search,
               jobs: list[JobDTO], errors: int = 0,
               blocked: bool = False) -> dict[str, Any]:
    """Persist a batch of scraped jobs for one search; return the scrape_run."""
    started = time.time()
    run = client.create("scrape_runs", {
        "keyword": search.keyword,
        "location": search.location,
        "jobs_found": 0, "jobs_new": 0, "jobs_updated": 0,
        "jobs_deactivated": 0, "errors": errors, "status": "running",
    })
    run_id = run["id"]

    # Existing jobs for this search, keyed by Indeed job key.
    existing = {
        r["indeed_jk"]: r
        for r in client.list_all("jobs", filter_=f'search_keyword="{search.keyword}"')
    }

    jobs_new = jobs_updated = 0
    seen: set[str] = set()
    now = _now_iso()

    for job in jobs:
        seen.add(job.indeed_jk)
        record = _dto_to_record(job)

        if job.indeed_jk not in existing:
            payload = {
                **record,
                "is_active": True,
                "first_seen_at": now,
                "last_seen_at": now,
                "search_keyword": search.keyword,
                "scrape_run": run_id,
            }
            try:
                client.create("jobs", payload)
                jobs_new += 1
            except Exception as e:  # noqa: BLE001
                logger.error("Failed to create job {}: {}", job.indeed_jk, e)
                errors += 1
            continue

        # Existing job: diff tracked fields -> snapshots, then update.
        prev = existing[job.indeed_jk]
        changes = _diff(prev, record)
        reactivated = not prev.get("is_active", False)
        try:
            client.update("jobs", prev["id"], {
                **record,
                "last_seen_at": now,
                "is_active": True,
                "scrape_run": run_id,
            })
            jobs_updated += 1
            for field_changed, old_v, new_v in changes:
                client.create("job_snapshots", {
                    "job": prev["id"], "field_changed": field_changed,
                    "old_value": old_v, "new_value": new_v,
                })
            if reactivated:
                client.create("job_snapshots", {
                    "job": prev["id"], "field_changed": "is_active",
                    "old_value": "false", "new_value": "true",
                })
        except Exception as e:  # noqa: BLE001
            logger.error("Failed to update job {}: {}", job.indeed_jk, e)
            errors += 1

    # Deactivate jobs that were active but not seen in this run.
    jobs_deactivated = 0
    for jk, rec in existing.items():
        if jk in seen or not rec.get("is_active", False):
            continue
        try:
            client.update("jobs", rec["id"], {"is_active": False, "last_seen_at": rec.get("last_seen_at")})
            client.create("job_snapshots", {
                "job": rec["id"], "field_changed": "is_active",
                "old_value": "true", "new_value": "false",
            })
            jobs_deactivated += 1
        except Exception as e:  # noqa: BLE001
            logger.error("Failed to deactivate job {}: {}", jk, e)
            errors += 1

    if blocked and jobs_new == 0 and jobs_updated == 0:
        status = "failed"
    elif blocked or errors > 0:
        status = "partial"
    else:
        status = "success"

    final = client.update("scrape_runs", run_id, {
        "jobs_found": len(seen),
        "jobs_new": jobs_new,
        "jobs_updated": jobs_updated,
        "jobs_deactivated": jobs_deactivated,
        "errors": errors,
        "duration_seconds": round(time.time() - started, 1),
        "status": status,
    })
    logger.info(
        "Run [{}] done: found={} new={} updated={} deactivated={} errors={} status={}",
        search.keyword, len(seen), jobs_new, jobs_updated, jobs_deactivated, errors, status,
    )
    return final
