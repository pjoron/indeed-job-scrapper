# indeed-job-scrapper

Scraper Indeed (France) ciblé sur le mot-clé **développeur full-stack**, avec stockage
PocketBase et **analyse de l'évolution dans le temps** (volume d'offres, salaires, top
entreprises, type de contrat & mode de travail).

## Architecture

```
config.py / searches.json # configuration + requêtes (mot-clé + localisation)
run.py # CLI : scrape | schedule | report
pb/setup_pocketbase.py # script d'init des collections PocketBase
scraper/ # Playwright furtif -> JobDTO (indeed.py, parser.py, models.py)
pipeline/ # PocketBase : client.py + store.py (upsert + diff temporel)
analysis/report.py # pandas + plotly -> rapport HTML
```

Le suivi temporel repose sur deux collections : `scrape_runs` (une ligne par exécution =
série du volume) et `job_snapshots` (un historique des changements de chaque offre).

## Installation

```bash
pip install -r requirements.txt
playwright install chromium
cp .env.example .env   # puis ajuster les identifiants superuser pb
```

## Usage

1. **Lancer PocketBase** (le binaire `pocketbase` est à mettre dans `pb/`) :

   ```bash
   cd pb && ./pocketbase serve
   ```

   Admin UI : http://127.0.0.1:8090/_/

2. **Initialiser les collections** :

   ```bash
   python pb/setup_pocketbase.py
   ```

3. **Scraper** une fois :

   ```bash
   python run.py scrape
   ```

4. **Planifier** (daemon, cadence `SCRAPE_INTERVAL_HOURS`, run immédiat au démarrage) :

   ```bash
   python run.py schedule
   ```

5. **Générer le rapport** d'analyse (`reports/report_<date>.html`) :

   ```bash
   python run.py report
   ```

## Configuration

- `searches.json` : liste de recherches `{ "keyword": ..., "location": ... }`. Par défaut
  une seule : `développeur full-stack` / `France`.
- `.env` : identifiants PocketBase + paramètres de scraping (`HEADLESS`, `MAX_PAGES`,
  `FETCH_DETAILS`, délais `MIN_DELAY`/`MAX_DELAY`) et cadence du scheduler.
