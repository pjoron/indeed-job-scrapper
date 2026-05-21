"""Stealth Playwright scraper for Indeed France."""

from __future__ import annotations

import random
import time
from typing import Iterator
from urllib.parse import quote_plus

from loguru import logger
from playwright.sync_api import Page, sync_playwright

from config import FETCH_DETAILS, HEADLESS, INDEED_BASE_URL, MAX_DELAY, MAX_PAGES, MIN_DELAY
from .models import JobDTO
from .parser import parse_detail_page, parse_search_page

_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

# Markers that indicate Indeed served a block / verification page.
_BLOCK_MARKERS = (
    "cf-challenge",
    "captcha",
    "verifying you are human",
    "vous êtes bien un humain",
    "additional verification required",
    "px-captcha",
)


class BlockedError(RuntimeError):
    """Raised when Indeed returns an anti-bot / verification page."""


def _apply_stealth(page: Page) -> None:
    """Apply playwright-stealth if available; tolerate API differences."""
    try:
        from playwright_stealth import Stealth  # newer API
        Stealth().apply_stealth_sync(page)
        return
    except Exception:
        pass
    try:
        from playwright_stealth import stealth_sync  # older API
        stealth_sync(page)
    except Exception:
        logger.debug("playwright-stealth unavailable; continuing without it.")


def _sleep_jitter() -> None:
    time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))


def _is_blocked(html: str) -> bool:
    low = html.lower()
    return any(marker in low for marker in _BLOCK_MARKERS)


def _search_url(keyword: str, location: str, start: int) -> str:
    return (
        f"{INDEED_BASE_URL}/jobs?q={quote_plus(keyword)}"
        f"&l={quote_plus(location)}&start={start}"
    )


def _get_html(page: Page, url: str) -> str:
    page.goto(url, wait_until="domcontentloaded", timeout=45000)
    _sleep_jitter()
    html = page.content()
    if _is_blocked(html):
        raise BlockedError(f"Anti-bot page detected at {url}")
    return html


def scrape_search(keyword: str, location: str = "France") -> Iterator[JobDTO]:
    """Yield JobDTOs for a (keyword, location) search.

    Raises BlockedError if Indeed blocks the very first page (nothing usable);
    later blocks are logged and stop pagination gracefully.
    """
    seen: set[str] = set()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS)
        context = browser.new_context(
            locale="fr-FR",
            user_agent=_USER_AGENT,
            viewport={"width": 1366, "height": 900},
            timezone_id="Europe/Paris",
        )
        page = context.new_page()
        _apply_stealth(page)

        try:
            for page_idx in range(MAX_PAGES):
                start = page_idx * 10
                url = _search_url(keyword, location, start)
                logger.info("Fetching search page {} ({})", page_idx + 1, url)
                try:
                    html = _get_html(page, url)
                except BlockedError as e:
                    if page_idx == 0:
                        raise
                    logger.warning("Stopping pagination: {}", e)
                    break

                jobs = parse_search_page(html, INDEED_BASE_URL)
                if not jobs:
                    logger.info("No more results at page {}; stopping.", page_idx + 1)
                    break

                new_on_page = 0
                for job in jobs:
                    if job.indeed_jk in seen:
                        continue
                    seen.add(job.indeed_jk)
                    new_on_page += 1

                    if FETCH_DETAILS:
                        try:
                            detail_html = _get_html(page, job.source_url)
                            detail = parse_detail_page(detail_html)
                            if detail.get("description"):
                                job.description = detail["description"]
                            if detail.get("salary_min") is not None:
                                job.salary_min = detail["salary_min"]
                                job.salary_max = detail["salary_max"]
                                job.salary_currency = detail["salary_currency"]
                                job.salary_period = detail["salary_period"]
                        except BlockedError as e:
                            logger.warning("Skipping detail for {}: {}", job.indeed_jk, e)
                    yield job

                logger.info("Page {}: {} new jobs", page_idx + 1, new_on_page)
                if new_on_page == 0:
                    break
        finally:
            context.close()
            browser.close()
