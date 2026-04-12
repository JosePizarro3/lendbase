# lendbase

A simple internal inventory and lending app for a university admin team.

Implementation notes, roadmap, and product decisions live in
[VIBE_NOTES.md](D:\REPOS\lendbase\VIBE_NOTES.md:1).

## What is currently in the repo

- Installable Python package with `src/` layout
- Flask app factory and environment-aware configuration
- Minimal home page and `/health` endpoint
- Pytest coverage for app startup
- GitHub Actions CI and pre-commit configuration

## Repository layout

```text
src/lendbase/
  app.py            Flask app factory
  config.py         Environment-aware settings
  web.py            Minimal web routes for the scaffold step
  templates/        Server-rendered HTML templates
  static/           Minimal styling assets
tests/
  test_app.py       Basic startup and health endpoint tests
```

## Requirements

- Python 3.12 or newer
- `uv` installed

You can use `pip` instead if needed, but the project now includes `uv.lock` and the
examples below use `uv`.

## Local setup

1. Create a virtual environment:

   ```cmd
   python -m venv .venv
   ```

2. Activate it:

   ```cmd
   .\.venv\Scripts\activate
   ```

3. Install dependencies:

   ```cmd
   uv sync --extra dev
   ```

4. Create a local environment file:

   ```cmd
   copy .env.example .env
   ```

## Environment configuration

Current environment variables:

- `LENDBASE_ENV`: `development`, `testing`, or `production`
- `LENDBASE_SECRET_KEY`: Flask session secret
- `LENDBASE_DATABASE_URL`: placeholder database URL for upcoming database work
- `LENDBASE_APP_BASE_URL`: base URL used later for links and QR generation

Example local `.env` values are provided in [.env.example](D:\REPOS\lendbase\.env.example:1).

## Initialize the database

Database initialization is not yet part of step 1.

The scaffold already exposes `LENDBASE_DATABASE_URL` and creates the Flask instance
directory so the next branch can add SQLAlchemy models and Alembic migrations without
reworking the app setup.

## Run locally

Use the Flask development server:

```cmd
set FLASK_APP=lendbase.app:create_app
python -m flask --debug run
```

Then open:

- `http://127.0.0.1:5000/`
- `http://127.0.0.1:5000/health`

## Login

Authentication is not implemented in this branch yet.

The shared admin login will be added in `feature/03-authentication` with secure
password hashing and a seed/bootstrap flow.

## Test instructions

Run the current automated tests with:

```cmd
uv run pytest -p no:cacheprovider
```

Current coverage is intentionally small and verifies:

- app factory startup
- home page rendering
- health endpoint behavior

## Automated checks

Local pre-commit checks:

```cmd
uv run pre-commit install
uv run pre-commit run --all-files
```

GitHub Actions also runs:

- pre-commit checks
- pytest

## Manual testing for this branch

1. Start the app locally.
2. Open the home page and confirm the scaffold page renders.
3. Open `/health` and confirm it returns JSON with status `ok`.
4. Change `.env` values and restart the app to confirm configuration is picked up.

## Debugging tips

Common issues in this step:

- Import errors usually mean dependencies were not installed with `uv sync --extra dev`.
- If `.env` changes are not visible, restart the Flask development server.
- If `uv` is missing, install it from Astral and rerun `uv sync --extra dev`.
- If you prefer not to activate the virtual environment, you can still run commands
  through `uv run`.

## Export data

Export is not implemented in this branch yet.

CSV export is planned for `feature/06-search-filter-export`. Excel import remains a
separate later migration task rather than a primary app UI feature.

## QR codes

QR generation is not implemented in this branch yet.

The scaffold already includes `LENDBASE_APP_BASE_URL` so later QR code generation can
resolve stable item URLs in local development and in institutional deployments.
