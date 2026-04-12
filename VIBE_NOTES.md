# VIBE_NOTES

Project notes, implementation sequence, and working assumptions live here so
`README.md` can stay focused on setup and operation.

## Product direction

- Internal browser-based inventory app for a small HU Berlin admin team
- English UI only
- One shared admin login for v1
- Local-first development and deployment assumptions
- Prioritize a practical, maintainable prototype over abstraction-heavy design

## Technical direction

- Flask server-rendered app
- SQL database with SQLAlchemy planned next
- Alembic migrations planned next
- Environment-based configuration from the start
- `uv` available for environment and dependency management
- `cmd`-friendly setup instructions preferred in docs

## Current implemented scope

- Python package scaffold with `src/` layout
- Flask app factory and configuration module
- Development, testing, and production config classes
- Minimal home page and `/health` endpoint
- SQLAlchemy ORM models for core inventory, lending, and audit entities
- Alembic migration setup with the initial schema
- Shared admin authentication with bootstrap-only account creation
- Browser-backed item CRUD with notes informed by the workbook in `data/`
- Browser-backed lending and return workflow on top of item detail pages
- Search by service tag, HU number, and serial number plus CSV export of filtered results
- Pytest coverage for startup paths
- GitHub Actions CI and pre-commit automation

## Incremental branch plan

1. `feature/01-scaffold-config`
   - Project scaffold
   - Dependency management
   - App factory and configuration module
   - Dev vs prod settings
   - Basic health page
   - README, `.env.example`, setup notes
   - CI workflow and pre-commit automation

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
   - Search by service tag, HU number, serial number
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

## Deferred by design

- Excel import is not part of the primary app UI in v1
- A one-off migration script should be added later under a dedicated import or
  scripts module
- Attachments are deferred for now but should remain easy to add later

## Production-readiness gaps to address later

- Replace shared-password auth with stronger authentication or SSO
- Run behind HTTPS and a reverse proxy
- Add database backup and restore procedures
- Expand audit coverage and operational access logging
- Move secrets into proper secret management
- Design attachment storage and retention rules
- Add multi-user accounts, permissions, and ownership rules
- Define deployment, monitoring, and maintenance procedures
