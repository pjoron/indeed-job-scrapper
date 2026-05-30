"""Build a self-contained HTML report (Plotly)"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from loguru import logger

from config import REPORTS_DIR
from pipeline.client import PocketBaseClient

# Annualisation factors to compare salaries on one scale.
_PERIOD_TO_YEAR = {"year": 1, "month": 12, "week": 52, "day": 220, "hour": 1800}


def _load_frames(client: PocketBaseClient) -> tuple[pd.DataFrame, pd.DataFrame]:
    runs = pd.DataFrame(client.list_all("scrape_runs"))
    jobs = pd.DataFrame(client.list_all("jobs"))
    if not runs.empty:
        runs["started_at"] = pd.to_datetime(runs["started_at"], errors="coerce")
    if not jobs.empty:
        for col in ("posted_at", "first_seen_at", "last_seen_at"):
            if col in jobs:
                jobs[col] = pd.to_datetime(jobs[col], errors="coerce")
        jobs["salary_annual"] = jobs.apply(_annual_salary, axis=1)
    return runs, jobs


def _annual_salary(row: pd.Series) -> float | None:
    lo, hi = row.get("salary_min"), row.get("salary_max")
    vals = [v for v in (lo, hi) if v not in (None, 0)]
    if not vals:
        return None
    mid = sum(vals) / len(vals)
    factor = _PERIOD_TO_YEAR.get(row.get("salary_period") or "year", 1)
    return mid * factor


def _fig_volume(runs: pd.DataFrame) -> go.Figure:
    if runs.empty:
        return _empty("Volume d'offres — aucune donnée")
    df = runs.sort_values("started_at")
    fig = go.Figure()
    for col, name in [("jobs_found", "Offres trouvées"),
                      ("jobs_new", "Nouvelles"),
                      ("jobs_deactivated", "Retirées")]:
        if col in df:
            fig.add_trace(go.Scatter(x=df["started_at"], y=df[col],
                                     mode="lines+markers", name=name))
    fig.update_layout(title="Volume d'offres dans le temps",
                      xaxis_title="Date du run", yaxis_title="Nombre d'offres")
    return fig


def _fig_salary(jobs: pd.DataFrame) -> go.Figure:
    if jobs.empty or jobs["salary_annual"].dropna().empty:
        return _empty("Salaires — aucune donnée salariale")
    df = jobs.dropna(subset=["salary_annual"]).copy()
    df = df[df["posted_at"].notna()]
    if df.empty:
        # Fall back to a plain distribution if no posted_at.
        return px.box(jobs.dropna(subset=["salary_annual"]), y="salary_annual",
                      points="all", title="Distribution des salaires (annualisés, €)")
    df["mois"] = df["posted_at"].dt.to_period("M").dt.to_timestamp()
    monthly = df.groupby("mois")["salary_annual"].median().reset_index()
    fig = px.line(monthly, x="mois", y="salary_annual", markers=True,
                  title="Salaire annuel médian par mois de publication (€)")
    fig.update_layout(xaxis_title="Mois", yaxis_title="Salaire annuel médian (€)")
    return fig


def _fig_companies(jobs: pd.DataFrame, top_n: int = 15) -> go.Figure:
    active = jobs[jobs.get("is_active", False) == True] if not jobs.empty else jobs  # noqa: E712
    if active.empty:
        return _empty("Top entreprises — aucune offre active")
    counts = active["company"].value_counts().head(top_n).reset_index()
    counts.columns = ["company", "offres"]
    fig = px.bar(counts, x="offres", y="company", orientation="h",
                 title=f"Top {top_n} entreprises (offres actives)")
    fig.update_layout(yaxis={"categoryorder": "total ascending"},
                      xaxis_title="Offres actives", yaxis_title="")
    return fig


def _fig_contract_remote(jobs: pd.DataFrame) -> go.Figure:
    from plotly.subplots import make_subplots
    active = jobs[jobs.get("is_active", False) == True] if not jobs.empty else jobs  # noqa: E712
    if active.empty:
        return _empty("Contrat & remote — aucune offre active")
    fig = make_subplots(rows=1, cols=2, specs=[[{"type": "pie"}, {"type": "pie"}]],
                        subplot_titles=("Type de contrat", "Mode de travail"))
    contract = active["contract_type"].fillna("Inconnu").value_counts()
    remote = active["remote"].fillna("Inconnu").value_counts()
    fig.add_trace(go.Pie(labels=contract.index, values=contract.values, name="Contrat"), 1, 1)
    fig.add_trace(go.Pie(labels=remote.index, values=remote.values, name="Remote"), 1, 2)
    fig.update_layout(title_text="Répartition contrat & mode de travail (offres actives)")
    return fig


def _empty(title: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text="Aucune donnée", showarrow=False, font={"size": 18})
    fig.update_layout(title=title, xaxis={"visible": False}, yaxis={"visible": False})
    return fig


def generate_report(client: PocketBaseClient | None = None) -> Path:
    """Generate reports/report_<date>.html and return its path."""
    own_client = client is None
    client = client or PocketBaseClient()
    try:
        runs, jobs = _load_frames(client)
        figures = [
            _fig_volume(runs),
            _fig_salary(jobs),
            _fig_companies(jobs),
            _fig_contract_remote(jobs),
        ]
    finally:
        if own_client:
            client.close()

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out = REPORTS_DIR / f"report_{date.today().isoformat()}.html"

    parts = [
        "<html><head><meta charset='utf-8'>"
        "<title>Rapport Indeed — développeur full-stack</title></head><body>",
        f"<h1>Rapport Indeed — {date.today().isoformat()}</h1>",
    ]
    for i, fig in enumerate(figures):
        parts.append(pio.to_html(fig, full_html=False,
                                 include_plotlyjs="cdn" if i == 0 else False))
    parts.append("</body></html>")

    out.write_text("\n".join(parts), encoding="utf-8")
    logger.info("Report written to {}", out)
    return out
