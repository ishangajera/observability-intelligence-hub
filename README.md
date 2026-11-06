# Signal Desk — Observability Intelligence Hub

A dark, searchable observability dashboard. GitHub Actions collects public RSS/Atom updates and GitHub releases, archives deduplicated JSON, and deploys this static site to GitHub Pages.

## Features
- Search, project/category filters, date sorting, release tracker, source directory
- RSS/Atom collection and GitHub release collection
- Daily automated collection and GitHub Pages deployment
- Versioned archive in `data/updates.json` and `data/meta.json`
- No database, server, paid API, or personal access token required

## Setup
1. In **Settings → Pages**, set **Build and deployment → Source** to **GitHub Actions**.
2. Open **Actions → Collect signals and deploy Signal Desk → Run workflow**.
3. After success, visit https://ishangajera.github.io/observability-intelligence-hub/

The workflow also runs daily at 13:20 UTC. GitHub Actions collection can be manually triggered at any time.

## Collection model
`config/sources.json` defines RSS/Atom feeds and GitHub repositories. `scripts/collect.py` normalizes titles, summaries and dates, deduplicates by URL, and writes up to 1,500 items. Some vendor blog landing pages may not expose RSS/Atom at that URL; failed feeds are logged and skipped. Update the configured URL to the vendor's feed endpoint when needed.

This is automated signal collection and publication, not AI-written editorial analysis. The dashboard does not claim to verify impact, assign severity, or provide migration advice. Open primary sources before acting.

## Local run
Requires Python 3.10+ and internet:
```bash
python scripts/collect.py
python -m http.server 8000
```
Open http://localhost:8000.

## Privacy
The repository and Pages site are public. Never commit private telemetry, customer data, credentials, tokens, or internal incident details. Workflow uses the repository-provided `GITHUB_TOKEN`.

## Layout
- `.github/workflows/collect-and-deploy.yml` — daily collection and deployment
- `assets/` — dashboard frontend
- `config/sources.json` — source registry
- `data/` — generated archive
- `scripts/collect.py` — collector
- `research/` — editorial reports (manual/AI-authored separately)
