# lendbase

A simple internal inventory and lending app for a university admin team.

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
