"""Clean data contract between the scraper and the storage pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass
class JobDTO:
    """A single Indeed job offer, normalised.

    `indeed_jk` is Indeed's stable job key and acts as the unique identity used
    for upserts and temporal diffing.
    """

    indeed_jk: str
    title: str
    company: str
    source_url: str

    location: Optional[str] = None
    remote: Optional[str] = None # remote | hybrid | onsite
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: Optional[str] = None
    salary_period: Optional[str] = None # year | month | week | day | hour
    contract_type: Optional[str] = None # CDI | CDD | Freelance | ...
    description: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    posted_at: Optional[date] = None
