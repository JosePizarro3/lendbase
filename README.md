# lendbase

A simple internal inventory and lending app for a university admin team.

Implementation notes, roadmap, and product decisions live in
[VIBE_NOTES.md](D:\REPOS\lendbase\VIBE_NOTES.md:1).

Schema extension guidance lives in
[docs/SCHEMA.md](D:\REPOS\lendbase\docs\SCHEMA.md:1).

## What is currently in the repo

- Installable Python package with `src/` layout
- Flask app factory and environment-aware configuration
- Minimal home page and `/health` endpoint
- SQLAlchemy models for items, lending records, and audit history
- Alembic migration setup with an initial schema migration
- Shared admin authentication with password hashing and session login
- Browser-backed item list, create, detail, and edit pages
- Item deletion from the detail page
- Lending and return workflow with borrower/date tracking
- Search, filtering, lent-out view, and CSV export
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
  inventory.py      Item list/detail/create/edit routes and validation
  web.py            Minimal web routes for the scaffold step
  templates/        Server-rendered HTML templates
  static/           Minimal styling assets
migrations/         Alembic configuration and migration scripts
docs/
  SCHEMA.md         Guide for extending item fields safely
tests/
  test_app.py       Startup, configuration, and DB wiring tests
  test_auth.py      Authentication and bootstrap flow tests
  test_inventory.py Item CRUD tests
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

Resetting the shared admin password:

```cmd
python -m flask --app lendbase.app:create_app reset-admin-password --username your-admin-name
```

The command prompts for the new password and confirmation without echoing the password
back to the terminal.

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
4. Open `/items` and create a first inventory item.
5. Open the item detail page and confirm the metadata is shown.
6. Edit the item and confirm the updated values persist.
7. Use the search box with a service tag, HU number, or serial number and confirm the list narrows correctly.
8. Filter by item type or status and confirm the table updates.
9. Open the `Currently lent out` quick view and confirm only lent items appear.
10. Export the current filtered list to CSV and inspect the file contents.
11. Lend an item and confirm borrower name, lent date, and comments appear on the detail page.
12. Register the item return and confirm its status changes back to `in storage`.
13. Delete an item from the detail page and confirm it disappears from `/items`.
14. Log out and verify `/items` redirects to `/login`.
15. Run the password reset command and confirm you can log in with the new password.
16. Open `/health` and confirm it returns JSON with status `ok`.
17. Confirm the SQLite database file exists in `instance\lendbase-dev.db`.
18. Change `.env` values and restart the app to confirm configuration is picked up.

## Debugging tips

Common issues in this step:

- Import errors usually mean dependencies were not installed with `uv sync --extra dev`.
- If `uv run alembic upgrade head` fails, check that `LENDBASE_DATABASE_URL` is set to
  a valid SQLAlchemy URL.
- If `/login` redirects to `/setup/admin`, the shared admin account has not been created yet.
- If the password reset command says the admin user was not found, verify the username in the database and the selected `.env` database path.
- If the edit page fails for an item with sparse metadata, verify you are on the latest branch revision with the optional-field form fix.
- If `.env` changes are not visible, restart the Flask development server.
- If `uv` is missing, install it from Astral and rerun `uv sync --extra dev`.
- If you prefer not to activate the virtual environment, you can still run commands
  through `uv run`.

## Export data

CSV export is implemented from the item list page.

The export uses the current search/filter/view state, so you can narrow the list first
and then export only the matching rows.

Excel import remains a separate later migration task rather than a primary app UI
feature.

The existing workbook in `data/` was used to guide the item field mapping for this
branch. Repeating core columns such as equipment, model, service tag, and HU inventory
number map cleanly to the English UI fields, while any extra sheet-specific remarks are
intended to land in `notes`.

Lending is now handled directly in the app by storing:

- borrower name
- lent date
- optional comments
- return date when the item comes back

## QR codes

QR generation is not implemented in this branch yet.

The scaffold already includes `LENDBASE_APP_BASE_URL` so later QR code generation can
resolve stable item URLs in local development and in institutional deployments.
