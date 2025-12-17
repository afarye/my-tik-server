<!-- .github/copilot-instructions.md: Guidance for AI coding agents working on this repo -->

# Quick Context

This repo is a FastAPI service that orchestrates a Scrapy/Playwright TikTok scraper.
Key pieces live under `app/` (the running service) and a duplicate `tiktok_scraper/` folder exists at repo root — prefer `app/tiktok_scraper` when changing server code.

# Big-picture architecture

- **API server:** `app/main.py` (FastAPI). Exposes endpoints under `/api` and a health check at `/health`.
  - On startup it calls `init_db()` from `app/tiktok_scraper/database/models.py` to create tables.
  - Database sessions are provided by the dependency generator `app/tiktok_scraper/database/db.py:get_db()`.
- **Scraper:** `app/tiktok_scraper/` is a Scrapy project configured to use Playwright (`settings.py`) and contains:
  - `spiders/tiktok_spider.py` — the `tiktok` spider used by the server.
  - `items.py` and `pipelines.py` — the simplest pipeline (`JsonPipeline`) that returns items as-is.
- **Orchestration:** `app/main.py` launches Scrapy as a subprocess (inside `app/`) with `-o output.json` and reads that JSON to persist records into `user_history` via SQLAlchemy models.

# Important files to reference

- `app/main.py` — request validation, scrapy subprocess invocation, and DB persistence logic.
- `app/tiktok_scraper/settings.py` — Scrapy + Playwright tuning (timeouts, concurrency, launch args).
- `app/tiktok_scraper/spiders/tiktok_spider.py` — how items are extracted and Playwright usage (page methods/meta fields).
- `app/tiktok_scraper/database/models.py` — SQLAlchemy models, default `DATABASE_URL` and `init_db()`.
- `app/tiktok_scraper/database/db.py` — `get_db()` DI generator used by FastAPI routes.
- `scripts/start.sh` — canonical way to run the server locally (`uvicorn app.main:app`).

# Developer workflows (concrete commands)

- Start API server (recommended):

  export PYTHONPATH=$(pwd):$PYTHONPATH
  ./scripts/start.sh

- Start server directly with Uvicorn:

  export PYTHONPATH=$(pwd):$PYTHONPATH
  python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000

- Run the Scrapy spider manually (from project root):

  cd app
  export PYTHONPATH=$(pwd):$PYTHONPATH
  python3 -m scrapy crawl tiktok -a urls="https://www.tiktok.com/@user" -o out.json -s SCRAPY_SETTINGS_MODULE=tiktok_scraper.settings

- Health & API docs (once server running):
  - Health: `http://localhost:8000/health`
  - Swagger UI: `http://localhost:8000/docs`

# Project-specific conventions & notes for code edits

- Use the `app/` package structure when editing server code—imports in `app/main.py` expect `app.tiktok_scraper.*`.
- The server generates `scrapy.cfg` in `app/` at runtime if missing (see `crawl_scrapy` endpoint). Changes to where Scrapy is invoked must preserve `PYTHONPATH` injection and `SCRAPY_SETTINGS_MODULE` env arg.
- Scrapy output: `main.py` expects `-o` produced JSON to be a list (or a single item coerced to list). Make sure pipeline output is JSON-serializable.
- Playwright: `settings.py` sets `PLAYWRIGHT_LAUNCH_OPTIONS` and uses `scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler`. Any changes to Playwright usage should keep the page meta contract used in `tiktok_spider.py` (e.g., `playwright_page`, `playwright_page_methods`).
- Database: models use env `DATABASE_URL`. Default is a local MySQL URL in `models.py`. `init_db()` is called on app startup — migrations are manual via `scripts/init_tables.py` and SQL under `app/tiktok_scraper/database/init.sql`/`scripts`.

# Where to look when debugging common issues

- Scrapy failures from `crawl_scrapy`: inspect subprocess `stderr` and `out.json` created in a temp dir. `app/main.py` logs first 500 chars of stderr on failure.
- DB connection problems: check `DATABASE_URL` env var and ensure the engine in `models.py` can connect. `get_db()` yields `SessionLocal()`.
- Playwright missing dependencies: Playwright must be installed and browsers installed (`playwright install` in environment used to run Scrapy).

# Examples for small code changes

- To add a new field persisted from spider -> DB:
  1. Add field to `app/tiktok_scraper/items.py` and populate in `spiders/tiktok_spider.py`.
  2. Make the field JSON-serializable in pipeline or spider output.
  3. Add column to `app/tiktok_scraper/database/models.py` and update `init_db()` (or run migration script).

- To change how Scrapy is invoked by the API: edit `app/main.py:crawl_scrapy` — preserve how `env["PYTHONPATH"]` and `-s SCRAPY_SETTINGS_MODULE=...` are set and ensure output path is readable by the server process.

# Quick checklist for pull requests

- Confirm edits target `app/` modules (not the duplicate top-level `tiktok_scraper/`) unless intentionally changing the standalone Scrapy project.
- Ensure `PYTHONPATH` usage is preserved for subprocess runs.
- If adding new dependencies, update `config/requirements.txt` and mention `playwright install` in PR description if relevant.

# Questions for the repo owner (if unclear)

- Which of the two `tiktok_scraper/` copies (root vs `app/`) should be considered canonical for future development?
- Are there CI tests or a preferred local dev DB (Docker compose in `config/`) that contributors should use?

---
If anything above is unclear or you want additional examples (e.g., a template PR checklist or example change), tell me which area to expand. 
