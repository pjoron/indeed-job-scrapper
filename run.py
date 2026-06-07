#!/usr/bin/env python3
"""CLI entrypoint for the Indeed scraper.

    python run.py scrape      # one full pass over all configured searches
    python run.py schedule    # run on an interval (APScheduler daemon)
    python run.py report      # generate the HTML analysis report
"""

from __future__ import annotations

import argparse
import sys

from loguru import logger

from analysis.report import generate_report
from config import SCRAPE_INTERVAL_HOURS, load_searches
from pipeline.client import PocketBaseClient
from pipeline.store import store_jobs
from scraper.indeed import BlockedError, scrape_search


def run_scrape() -> None:
    searches = load_searches()
    logger.info("Starting scrape for {} search(es)", len(searches))
    with PocketBaseClient() as client:
        for search in searches:
            blocked = False
            errors = 0
            jobs = []
            try:
                jobs = list(scrape_search(search.keyword, search.location))
            except BlockedError as e:
                logger.error("Search '{}' blocked by Indeed: {}", search.keyword, e)
                blocked = True
            except Exception as e:  # noqa: BLE001
                logger.exception("Search '{}' failed: {}", search.keyword, e)
                errors += 1
            store_jobs(client, search, jobs, errors=errors, blocked=blocked)


def run_schedule() -> None:
    from apscheduler.schedulers.blocking import BlockingScheduler

    scheduler = BlockingScheduler(timezone="Europe/Paris")
    scheduler.add_job(run_scrape, "interval", hours=SCRAPE_INTERVAL_HOURS,
                      next_run_time=None, id="indeed_scrape")
    logger.info("Scheduler started (every {} h). Running an initial scrape now.",
                SCRAPE_INTERVAL_HOURS)
    run_scrape()  # immediate first run
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped.")


def run_report() -> None:
    path = generate_report()
    print(f"Report generated: {path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Indeed job scraper + temporal analysis")
    parser.add_argument("command", choices=["scrape", "schedule", "report"])
    args = parser.parse_args()

    if args.command == "scrape":
        run_scrape()
    elif args.command == "schedule":
        run_schedule()
    elif args.command == "report":
        run_report()
    else:  # pragma: no cover
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
