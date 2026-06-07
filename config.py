import json
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent

# PocketBase
PB_URL = os.getenv("PB_URL", "http://127.0.0.1:8090").rstrip("/")
PB_SUPERUSER_EMAIL = os.getenv("PB_SUPERUSER_EMAIL", "")
PB_SUPERUSER_PASSWORD = os.getenv("PB_SUPERUSER_PASSWORD", "")

# Scraping
INDEED_BASE_URL = os.getenv("INDEED_BASE_URL", "https://fr.indeed.com")
HEADLESS = os.getenv("HEADLESS", "true").lower() in ("1", "true", "yes")
MAX_PAGES = int(os.getenv("MAX_PAGES", "10")) # search result pages per query
FETCH_DETAILS = os.getenv("FETCH_DETAILS", "true").lower() in ("1", "true", "yes")
MIN_DELAY = float(os.getenv("MIN_DELAY", "2.0")) # seconds between requests (lower bound)
MAX_DELAY = float(os.getenv("MAX_DELAY", "5.0")) # seconds between requests (upper bound)

# Scheduler
SCRAPE_INTERVAL_HOURS = float(os.getenv("SCRAPE_INTERVAL_HOURS", "24"))

# Reports
REPORTS_DIR = ROOT / "reports"
SEARCHES_FILE = ROOT / "searches.json"


@dataclass(frozen=True)
class Search:
    keyword: str
    location: str = "France"


def load_searches() -> list[Search]:
    """Load the list of (keyword, location) searches from searches.json."""
    if not SEARCHES_FILE.exists():
        return [Search(keyword="développeur full-stack", location="France")]
    raw = json.loads(SEARCHES_FILE.read_text(encoding="utf-8"))
    return [Search(keyword=s["keyword"], location=s.get("location", "France")) for s in raw]
