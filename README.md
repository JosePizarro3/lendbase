# lendbase

A simple internal inventory and lending app for a university admin team.

Implementation notes, roadmap, and product decisions live in
[VIBE_NOTES.md](D:\REPOS\lendbase\VIBE_NOTES.md:1).

## What is currently in the repo

- Installable Python package with `src/` layout
- Flask app factory and environment-aware configuration
- Minimal home page and `/health` endpoint
- SQLAlchemy models for items, lending records, and audit history
- Alembic migration setup with an initial schema migration
- Shared admin authentication with password hashing and session login
- Pytest coverage for app startup
- GitHub Actions CI and pre-commit configuration

## Repository layout

```text
src/lendbase/
  app.py            Flask app factory
  config.py         Environment-aware settings
  db.py             Database engine/session setup
  models.py         SQLAlchemy models
  auth.py           Login, logout, and admin bootstrap flow
  web.py            Minimal web routes for the scaffold step
  templates/        Server-rendered HTML templates
  static/           Minimal styling assets
migrations/         Alembic configuration and migration scripts
tests/
  test_app.py       Startup, configuration, and DB wiring tests
  test_auth.py      Authentication and bootstrap flow tests
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

Initialize the local database with:

```cmd
uv run alembic upgrade head
```

For the default SQLite setup, the database file is created under the Flask instance
directory as `instance/lendbase-dev.db`.

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

Authentication is now implemented as a simple shared-admin flow.

First-time setup:

1. Run `uv run alembic upgrade head`
2. Open `http://127.0.0.1:5000/setup/admin`
3. Create the shared admin username and password
4. Use those credentials on `http://127.0.0.1:5000/login`

Notes:

- Passwords are stored as secure hashes, not plaintext
- The bootstrap route is disabled after the first admin account is created
- Browser-facing app routes require a logged-in admin session

## Test instructions

Run the current automated tests with:

```cmd
uv run pytest -p no:cacheprovider
```

Current coverage is intentionally small and verifies:

- app factory startup
- home page rendering
- health endpoint behavior
- database wiring and SQLite path resolution
- admin bootstrap, login, logout, and route protection

## Automated checks

Local pre-commit checks:

```cmd
uv run pre-commit install
uv run pre-commit run --all-files
```

GitHub Actions also runs:

- pre-commit checks
- pytest
- the same `uv`-based dependency sync used locally

## Manual testing for this branch

1. Start the app locally.
2. Run `uv run alembic upgrade head`.
3. Open `/setup/admin` and create the first admin account.
4. Open the home page and confirm the authenticated dashboard page renders.
5. Log out and verify `/` redirects to `/login`.
6. Open `/health` and confirm it returns JSON with status `ok`.
7. Confirm the SQLite database file exists in `instance\lendbase-dev.db`.
8. Change `.env` values and restart the app to confirm configuration is picked up.

## Debugging tips

Common issues in this step:

- Import errors usually mean dependencies were not installed with `uv sync --extra dev`.
- If `uv run alembic upgrade head` fails, check that `LENDBASE_DATABASE_URL` is set to
  a valid SQLAlchemy URL.
- If `/login` redirects to `/setup/admin`, the shared admin account has not been created yet.
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
