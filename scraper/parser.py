from __future__ import annotations

import json
import re
from datetime import date, timedelta
from typing import Any, Optional

from bs4 import BeautifulSoup

from .models import JobDTO

# regexes

_MOSAIC_RE = re.compile(
    r'window\.mosaic\.providerData\["mosaic-provider-jobcards"\]\s*=\s*(\{.*?\});',
    re.DOTALL,
)

_NUM_RE = re.compile(r"(\d[\d\s.,]*)")

_CONTRACT_MAP = {
    "cdi": "CDI",
    "permanent": "CDI",
    "temps plein": "CDI",
    "cdd": "CDD",
    "temporary": "CDD",
    "freelance": "Freelance",
    "indépendant": "Freelance",
    "stage": "Stage",
    "internship": "Stage",
    "alternance": "Alternance",
    "apprenticeship": "Alternance",
    "apprentissage": "Alternance",
    "intérim": "Interim",
    "interim": "Interim",
}

_PERIOD_MAP = {
    "an": "year", "année": "year", "ans": "year", "year": "year",
    "mois": "month", "month": "month",
    "semaine": "week", "week": "week",
    "jour": "day", "day": "day",
    "heure": "hour", "hour": "hour", "hr": "hour",
}


# normalisation helpers

def _to_number(raw: str) -> Optional[float]:
    m = _NUM_RE.search(raw)
    if not m:
        return None
    cleaned = m.group(1).replace(" ", "").replace(" ", "").replace("\xa0", "")
    cleaned = cleaned.replace(",", ".")
    parts = cleaned.split(".")
    if len(parts) > 1 and all(len(p) == 3 for p in parts[1:]):
        cleaned = "".join(parts)
    else:
        cleaned = parts[0] + ("." + parts[1] if len(parts) > 1 else "")
    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_salary(text: Optional[str]) -> dict[str, Any]:
    """Parse a salary snippet like '45 000 € - 55 000 € par an' into components."""
    out: dict[str, Any] = {"salary_min": None, "salary_max": None,
                           "salary_currency": None, "salary_period": None}
    if not text:
        return out
    low = text.lower()

    if "€" in text or "eur" in low:
        out["salary_currency"] = "EUR"
    elif "$" in text:
        out["salary_currency"] = "USD"
    elif "£" in text:
        out["salary_currency"] = "GBP"

    for token, period in _PERIOD_MAP.items():
        if re.search(rf"\bpar\s+{token}\b|\b{token}\b", low):
            out["salary_period"] = period
            break

    # numbers (one or two). Strip the period words first to avoid catching them.
    nums = [_to_number(n) for n in _NUM_RE.findall(text)]
    nums = [n for n in nums if n is not None]
    if len(nums) >= 2:
        out["salary_min"], out["salary_max"] = min(nums[0], nums[1]), max(nums[0], nums[1])
    elif len(nums) == 1:
        out["salary_min"] = out["salary_max"] = nums[0]
    return out


def parse_contract(values: list[str]) -> Optional[str]:
    for v in values:
        if not v:
            continue
        low = v.lower()
        for token, label in _CONTRACT_MAP.items():
            if token in low:
                return label
    return "Autre" if values else None


def parse_remote(text: Any) -> Optional[str]:
    if text is None or text == "":
        return None
    if isinstance(text, bool):
        return "remote" if text else None
    low = str(text).lower()
    if "hybrid" in low or "hybride" in low:
        return "hybrid"
    if "télétravail" in low or "remote" in low or "à distance" in low:
        return "remote"
    return None


def parse_posted_at(text: Optional[str], today: Optional[date] = None) -> Optional[date]:
    """Convert 'il y a 3 jours' / 'Publié il y a 30+ jours' / "aujourd'hui'."""
    if not text:
        return None
    today = today or date.today()
    low = text.lower()
    if "aujourd" in low or "just posted" in low or "à l'instant" in low:
        return today
    if "hier" in low:
        return today - timedelta(days=1)
    m = re.search(r"(\d+)\s*(jour|day|semaine|week|mois|month)", low)
    if not m:
        return None
    n = int(m.group(1))
    unit = m.group(2)
    if unit in ("jour", "day"):
        return today - timedelta(days=n)
    if unit in ("semaine", "week"):
        return today - timedelta(weeks=n)
    if unit in ("mois", "month"):
        return today - timedelta(days=30 * n)
    return None


# page parsers

def _extract_mosaic(html: str) -> list[dict]:
    """Return the raw job-card dicts from the embedded mosaic JSON."""
    m = _MOSAIC_RE.search(html)
    if not m:
        return []
    try:
        data = json.loads(m.group(1))
    except json.JSONDecodeError:
        return []
    try:
        return (data["metaData"]["mosaicProviderJobCardsModel"]["results"]) or []
    except (KeyError, TypeError):
        return []


def parse_search_page(html: str, base_url: str) -> list[JobDTO]:
    """Parse a search results page into JobDTOs (without full description)."""
    jobs: list[JobDTO] = []
    for card in _extract_mosaic(html):
        jk = card.get("jobkey") or card.get("jobKey")
        if not jk:
            continue
        title = card.get("displayTitle") or card.get("title") or ""
        company = card.get("company") or card.get("companyName") or ""
        location = card.get("formattedLocation") or card.get("jobLocationCity") or None

        salary_text = None
        snippet = card.get("salarySnippet") or card.get("estimatedSalary")
        if isinstance(snippet, dict):
            salary_text = snippet.get("text") or snippet.get("salaryText")
        elif isinstance(snippet, str):
            salary_text = snippet
        salary = parse_salary(salary_text)

        job_types = card.get("jobTypes") or []
        if isinstance(job_types, str):
            job_types = [job_types]
        # taxonomyAttributes sometimes carries job-type labels
        for attr in card.get("taxonomyAttributes", []) or []:
            if attr.get("label", "").lower() in ("job-types", "type d'emploi"):
                job_types += [a.get("label", "") for a in attr.get("attributes", [])]

        remote_text = card.get("remoteLocation") or card.get("remoteWorkModel") or ""
        if isinstance(remote_text, dict):
            remote_text = remote_text.get("text", "") or remote_text.get("type", "")

        posted = parse_posted_at(card.get("formattedRelativeTime") or card.get("relativeTime"))

        jobs.append(
            JobDTO(
                indeed_jk=jk,
                title=title.strip(),
                company=company.strip(),
                source_url=f"{base_url}/viewjob?jk={jk}",
                location=location,
                remote=parse_remote(remote_text) or "onsite",
                salary_min=salary["salary_min"],
                salary_max=salary["salary_max"],
                salary_currency=salary["salary_currency"],
                salary_period=salary["salary_period"],
                contract_type=parse_contract(job_types),
                posted_at=posted,
            )
        )
    return jobs


def parse_detail_page(html: str) -> dict[str, Any]:
    """Extract description (and refine salary) from a viewjob page."""
    out: dict[str, Any] = {"description": None}
    soup = BeautifulSoup(html, "html.parser")

    desc = soup.select_one("#jobDescriptionText")
    if desc:
        out["description"] = desc.get_text("\n", strip=True)

    salary_el = soup.select_one("#salaryInfoAndJobType, [data-testid='jobsearch-OtherJobDetailsContainer']")
    if salary_el:
        salary = parse_salary(salary_el.get_text(" ", strip=True))
        if salary["salary_min"] is not None:
            out.update(salary)
    return out
