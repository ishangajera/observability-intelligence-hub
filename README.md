# Signal Desk — Observability Intelligence Hub

A dark, searchable observability dashboard. GitHub Actions collects public RSS/Atom updates and GitHub releases, archives deduplicated JSON, adds transparent editorial triage, and deploys the static site to GitHub Pages.

## Features
- Search, project/category filters, date sorting, release tracker, source directory
- Automated RSS/Atom and GitHub release collection
- Rules-based editorial triage: attention level, detected themes, matched source evidence, and conservative review checklist
- Daily GitHub Actions collection and GitHub Pages deployment
- Versioned archive in `data/updates.json`, `data/meta.json`, and `data/intelligence.json`
- No database, server, paid API, or personal access token required

## Editorial triage: what it does and does not do
`scripts/enrich.py` scans collected titles and summaries for explicit language associated with security, breaking changes, deprecations, compatibility, performance, configuration, features, and bug fixes. It records matched text snippets and suggests review steps.

The priority label is an **attention cue**, not product severity. The system does not know whether a particular component is deployed in your environment, does not verify exploitability or operational impact, and does not generate product-specific migration instructions. A phrase match can be a false positive; missing a phrase does not mean a change is safe. Always inspect the linked primary source before acting.

This first editorial layer is intentionally deterministic and auditable. It does not call an LLM or send collected content to a third party.

## Setup
1. In **Settings → Pages**, set **Build and deployment → Source** to **GitHub Actions**.
2. Open **Actions → Collect signals and deploy Signal Desk → Run workflow**.
3. After success, visit https://ishangajera.github.io/observability-intelligence-hub/

The workflow also runs daily at 13:20 UTC.

## Collection model
`config/sources.json` defines RSS/Atom feeds and GitHub repositories. `scripts/collect.py` normalizes titles, summaries and dates, deduplicates by URL, and writes up to 1,500 items. Some vendor blog landing pages may not expose RSS/Atom at that URL; failed feeds are logged and skipped.

## Local run
Requires Python 3.10+ and internet:
```bash
python scripts/collect.py
python scripts/enrich.py
python -m http.server 8000
```
Open http://localhost:8000.

## Privacy
The repository and Pages site are public. Never commit private telemetry, customer data, credentials, tokens, or internal incident details. Workflow uses the repository-provided `GITHUB_TOKEN`.

## Layout
- `.github/workflows/collect-and-deploy.yml` — daily collection, triage, and deployment
- `assets/` — dashboard frontend
- `config/sources.json` — source registry
- `data/` — generated collection and triage archives
- `scripts/collect.py` — collector
- `scripts/enrich.py` — transparent editorial triage
