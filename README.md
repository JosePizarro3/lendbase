# lendbase

A simple internal inventory and lending app for a university admin team.

* Implementation notes, roadmap, and product decisions live with Codex in
[docs/VIBE_NOTES.md](docs/VIBE_NOTES.md).
* Schema extension guidance lives in
[docs/SCHEMA.md](docs/SCHEMA.md).
* Production hardening guidance lives in
[docs/PROD_READY.md](docs/PROD_READY.md).

## What is currently in the repo

- Installable Python package with `src/` layout
- Flask app factory and environment-aware configuration
- Home page with inventory summary and quick actions plus `/health`
- SQLAlchemy models for items, lending records, and audit history
- Alembic migration setup with an initial schema migration
- Shared admin authentication with password hashing and session login
- Browser-backed item list, create, detail, and edit pages
- Item deletion from the detail page
- Lending and return workflow with borrower/date tracking
- Search, filtering, lent-out view, and CSV export
- Clearer audit history with change details on the item page
- Item-level QR code generation with SVG and PNG download options
- Pytest coverage for app startup
- GitHub Actions CI and pre-commit configuration

## Requirements

- Python 3.12 or newer
- `uv` installed

You can use `pip` instead if needed, but the project includes `uv.lock` and the
examples below use `uv` in Windows.

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

## Environment configuration

Current environment variables:

- `LENDBASE_ENV`: `development`, `testing`, or `production`
- `LENDBASE_SECRET_KEY`: Flask session secret
- `LENDBASE_DATABASE_URL`: SQLAlchemy database URL
- `LENDBASE_APP_BASE_URL`: base URL used later for links and QR generation

Example local `.env` values are provided in [.env.example](.env.example). You can simply create a local environment file by doing:
```cmd
copy .env.example .env
```

## Initialize the database

Initialize the local database with:

```cmd
uv run alembic upgrade head
```

For the default SQLite setup, the database file is created under the project directory as `instance/lendbase-dev.db`.

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

Authentication is implemented as a simple shared-admin flow. 

First-time setup:

1. Run `uv run alembic upgrade head`
2. Open `http://127.0.0.1:5000/setup/admin`
3. Create the shared admin username and password
4. Use those credentials on `http://127.0.0.1:5000/login`

<!-- Notes:

- Passwords are stored as secure hashes, not plaintext
- The bootstrap route is disabled after the first admin account is created
- Browser-facing app routes require a logged-in admin session -->

With the admin credentials, you can reset the shared admin password:

```cmd
python -m flask --app lendbase.app:create_app reset-admin-password --username your-admin-name
```

## Test instructions

Run the current automated tests with:

```cmd
uv run pytest -p no:cacheprovider
```

Current coverage verifies:

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

## Manual testing

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
12. Confirm the audit history shows the lend event and the status change.
13. Register the item return and confirm its status changes back to `in storage`.
14. Confirm the audit history shows the return event and the status change.
15. Open the item detail page QR section and confirm the QR image renders beside the audit history.
16. Use the QR section buttons and confirm both SVG and PNG downloads work.
17. Open the QR SVG directly and confirm it loads.
18. Check that the displayed QR target URL matches `LENDBASE_APP_BASE_URL`.
19. Delete an item from the detail page and confirm it disappears from `/items`.
20. Log out and verify `/items` redirects to `/login`.
21. Run the password reset command and confirm you can log in with the new password.
22. Open `/health` and confirm it returns JSON with status `ok`.
23. Confirm the SQLite database file exists in `instance\lendbase-dev.db`.
24. Change `.env` values and restart the app to confirm configuration is picked up.

## Debugging tips

Common issues:

- Import errors usually mean dependencies were not installed with `uv sync --extra dev`.
- If `uv run alembic upgrade head` fails, check that `LENDBASE_DATABASE_URL` is set to a valid SQLAlchemy URL.
- If `/login` redirects to `/setup/admin`, the shared admin account has not been created yet.
- If the password reset command says the admin user was not found, verify the username in the database and the selected `.env` database path.
- If the edit page fails for an item with sparse metadata, verify you are on the latest branch revision with the optional-field form fix.
- If `.env` changes are not visible, restart the Flask development server.
- If `uv` is missing, install it from Astral and rerun `uv sync --extra dev`.
- If you prefer not to activate the virtual environment, you can still run commands through `uv run`.

## Export data

CSV export is implemented from the item list page.

The export uses the current search/filter/view state, so you can narrow the list first
and then export only the matching rows.

Excel import remains a separate later migration task rather than a primary app UI
feature.

Lending is handled directly in the app by storing:

- borrower name
- lent date
- optional comments
- return date when the item comes back

## QR codes

QR generation is implemented on each item detail page.

The QR target URL is built from:

- `LENDBASE_APP_BASE_URL`
- the item detail path

The page shows the QR as SVG for crisp in-browser display and offers explicit download
links for both SVG and PNG.

In local development, this usually means:

- QR target like `http://127.0.0.1:5000/items/123`
- scan leads to login first if no authenticated session exists

Before a real deployment, set `LENDBASE_APP_BASE_URL` to the final internal hostname so
printed codes resolve to the institution-facing URL.
