# lendbase

A simple internal inventory and lending app for a university admin team.

## Current status

Branch `feature/01-scaffold-config` sets up the initial runnable application skeleton.
This step intentionally keeps the functionality small while establishing the project
shape for later database, auth, inventory, lending, export, history, and QR work.

## Step 1 scope

This branch adds:

- Installable Python package with `src/` layout
- Flask app factory for a simple server-rendered internal web app
- Development, testing, and production configuration classes
- Environment variable loading via `.env`
- Minimal UI home page and JSON health endpoint
- Initial pytest coverage for app startup
- Documentation for setup, running, testing, and debugging

## Architecture choice

The v1 prototype uses Flask with server-rendered templates.

Why this is the default:

- Easy for an internal IT team to inspect
- Small dependency footprint
- Fast to iterate on for CRUD-heavy admin workflows
- Easy to harden later behind a reverse proxy, SSO layer, or institutional deployment
- Keeps the code approachable while still supporting clean app structure

Planned next additions:

- SQLAlchemy and Alembic for database and migrations
- Session-based authentication with secure password hashing
- Inventory item CRUD, lending workflows, search/filter/export, audit history, and QR codes

## Planned PR / branch sequence

This repository will be built in small, reviewable steps. Each branch should keep
the app runnable and update documentation as needed.

### Assumptions for v1

- Internal browser-based app
- English-only UI
- One shared admin account for now
- Local-first developer experience
- Simple server-rendered architecture preferred over frontend-heavy complexity

### Proposed implementation stack

- Python web backend
- SQL database via SQLAlchemy
- Alembic migrations
- Server-rendered HTML templates
- Minimal CSS/JS for usability
- Environment-based configuration for dev vs prod

### Incremental branches

1. `feature/01-scaffold-config`
   - Project scaffold
   - Dependency management
   - App factory and configuration module
   - Dev vs prod settings
   - Basic health page
   - README, `.env.example`, setup notes

2. `feature/02-db-models-migrations`
   - Database setup
   - Core models for items, lending records, and audit history
   - Initial Alembic migration
   - Database initialization instructions

3. `feature/03-authentication`
   - Shared admin login
   - Password hashing
   - Session-based auth
   - Seed/admin bootstrap flow

4. `feature/04-item-crud`
   - Item list and detail pages
   - Create/edit item forms
   - Validation for required fields

5. `feature/05-lending-return-workflow`
   - Lend item flow
   - Return item flow
   - Repeat lending support
   - Status coordination with lending state

6. `feature/06-search-filter-export`
   - Search by inventory number, HU number, serial number
   - Filter by item type and status
   - "Currently lent out" view
   - CSV export

7. `feature/07-audit-history`
   - Complete audit/event trail
   - Item history view improvements
   - Consistent event recording across workflows

8. `feature/08-qr-codes`
   - QR generation per item
   - Printable QR target URLs
   - Local/dev URL strategy with configurable base URL

9. `feature/09-polish-deployment-notes`
   - UX cleanup
   - Debugging notes
   - Test guide
   - Production readiness gaps and deployment considerations

### Notes for later

- Excel import stays out of the primary app UI in v1
- A one-off migration script should be added later under a dedicated import/migration
  module or scripts directory
- Attachments are intentionally deferred but the data model and app structure should
  remain easy to extend

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
- `pip` available in your chosen virtual environment

## Local setup

1. Create a virtual environment:

   ```cmd
   python -m venv .venv
   ```

2. Activate it:

   ```cmd
   .\.venv\Scripts\activate
   ```

3. Install the project in editable mode with developer dependencies:

   ```cmd
   uv pip install -e ".[dev]"
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

```powershell
python -m pytest
```

Current coverage is intentionally small and verifies:

- app factory startup
- home page rendering
- health endpoint behavior

## Manual testing for this branch

1. Start the app locally.
2. Open the home page and confirm the scaffold page renders.
3. Open `/health` and confirm it returns JSON with status `ok`.
4. Change `.env` values and restart the app to confirm configuration is picked up.

## Debugging tips

Common issues in this step:

- Import errors usually mean the project was not installed with `pip install -e ".[dev]"`.
- If `.env` changes are not visible, restart the Flask development server.
- If PowerShell blocks virtual environment activation, run:

  ```powershell
  Set-ExecutionPolicy -Scope Process RemoteSigned
  ```

- If `py -3.11` is unavailable, use any installed Python 3.11+ interpreter.
- On the current development machine, `py -3.12` is available and works for setup.

## Export data

Export is not implemented in this branch yet.

CSV export is planned for `feature/06-search-filter-export`. Excel import remains a
separate later migration task rather than a primary app UI feature.

## QR codes

QR generation is not implemented in this branch yet.

The scaffold already includes `LENDBASE_APP_BASE_URL` so later QR code generation can
resolve stable item URLs in local development and in institutional deployments.

## What remains intentionally simple in v1

- Single shared admin account
- Session-based app auth instead of institutional SSO
- Local-first deployment assumptions
- Minimal frontend without a separate SPA
- CSV export before richer reporting/import tooling

## Production readiness gaps

Before institutional production deployment, likely next steps include:

- Replace shared-password auth with stronger authentication or SSO
- Run behind HTTPS and a reverse proxy
- Add database backup and restore procedures
- Expand audit coverage and operational access logging
- Move secrets into proper secret management
- Design attachment storage and retention rules
- Add multi-user accounts, permissions, and ownership rules
- Define deployment, monitoring, and maintenance procedures
