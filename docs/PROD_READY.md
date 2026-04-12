# Production Readiness Guide

This document describes the main steps for taking `lendbase` from the current local-first
prototype into a more institutional deployment.

## Current v1 assumptions

The app is intentionally simple:

- one shared admin account
- Flask server-rendered UI
- SQLite by default for local use
- local `.env` file for secrets and configuration
- no attachment storage yet
- minimal operational logging

That is a reasonable starting point for proving the workflow, but it is not the final
shape for a university-managed deployment.

## Recommended deployment approach

The safest next step is:

1. keep the application itself boring and simple
2. run it behind a reverse proxy with HTTPS
3. move to PostgreSQL or another IT-approved SQL database
4. replace shared-login auth with institutional SSO
5. define backups, restore checks, and operational ownership

For most institutional environments, a good target shape is:

- `Flask app` served by Gunicorn or another production WSGI server
- `Reverse proxy` such as Nginx, Apache, or an institutional ingress layer
- `Managed SQL database`
- `Environment-specific configuration`
- `Central log collection`

## Should deployment center on Docker?

Short answer: a `Dockerfile` is worth adding, but the deployment strategy should not depend
entirely on Docker unless the university IT environment already prefers it.

Recommended position:

- Yes, add a `Dockerfile` later because it improves reproducibility, local parity, and CI.
- No, do not make Docker the only supported production path unless operations has already
  chosen a container-based platform.

Why a `Dockerfile` still helps:

- standardizes runtime dependencies
- makes local smoke testing easier
- gives CI and staging a predictable execution environment
- provides a clean handoff artifact for IT teams that use containers

Why not center everything around Docker by default:

- some university IT teams prefer VMs, systemd services, or existing web server stacks
- secrets, backups, HTTPS, and monitoring still need to be solved outside the container
- a container image alone does not answer institutional ownership and operations questions

Practical recommendation:

- Treat a `Dockerfile` as a supported packaging option.
- Keep the app deployable without Docker as well.
- Let institutional hosting constraints decide whether production uses containers.

## Authentication and access

Current state:

- one shared admin password

Recommended next step:

- replace the shared login with university SSO or a central identity provider

Good targets:

- Shibboleth
- OIDC
- SAML
- another institution-approved SSO flow

Minimum goals:

- individual user identities
- ability to disable access per person
- clearer attribution in audit history

Later role split:

- admin
- inventory manager
- read-only reviewer

## Database and backups

Current state:

- SQLite is fine for local development and early internal testing

Recommended production path:

- move to PostgreSQL or another approved relational database

Benefits:

- stronger concurrency support
- better backup tooling
- easier operational monitoring
- clearer path for managed infrastructure

Operational requirements:

- scheduled backups
- tested restore procedure
- retention policy
- owner for migrations and upgrade windows

## Secrets and configuration

Current state:

- `.env` file with local secrets

Recommended production path:

- move secrets into an institutional secret store or deployment platform secret manager

Examples:

- environment injection by IT platform
- Vault
- Kubernetes secrets
- another approved internal mechanism

At minimum, do not keep production secrets in the repo or in manually copied local files.

## HTTPS and serving

Current state:

- Flask development server

Recommended production path:

- production WSGI server
- reverse proxy or ingress
- HTTPS termination
- trusted host configuration

Suggested responsibilities:

- app process serves Flask
- reverse proxy handles HTTPS, headers, and request limits
- institution manages DNS and certificate rotation

## Logging, audit, and monitoring

Current state:

- item-level audit history for business actions
- minimal operational logging

Recommended next steps:

- structured application logs
- request logs
- failed login logging
- central log aggregation
- alerts for repeated failures or app downtime

Business audit improvements worth adding later:

- record which authenticated user made each change
- explicit login and logout events if policy requires them
- export actions in the audit trail if needed by the team

## Attachments and file storage

Current state:

- attachments are deferred

Before implementing them, decide:

- where files are stored
- who can access them
- whether files contain personal data
- retention rules
- backup coverage

Likely options:

- database is not ideal for larger files
- filesystem storage can work for small internal deployments
- object storage is better if the app grows

## Multi-user support and permissions

Current state:

- one shared admin account

Recommended later improvements:

- per-user accounts
- role-based permissions
- disable rather than delete users
- user attribution on item changes

This becomes much easier once SSO is in place.

## CI/CD and release process

Current state:

- GitHub Actions runs linting and tests

Recommended next steps:

- add a production dependency install check
- add a smoke test for migrations
- add a build artifact path if Docker is introduced
- define release tagging and rollback procedure

Simple release flow:

1. merge reviewed branch
2. run CI
3. deploy to staging
4. run smoke test
5. deploy to production
6. verify app health and a basic login flow

## What I would implement next

If the goal is a smoother and more durable pipeline, the most useful next additions are:

1. per-user authentication or SSO integration
2. PostgreSQL support for non-local deployment
3. a `Dockerfile` plus a simple production run command
4. a small import script for the existing Excel workbook
5. a seed or bootstrap command for first-run setup in staging and production

If you want the highest practical payoff with the least complexity, I would prioritize:

1. Excel migration script
2. Dockerfile
3. PostgreSQL configuration
4. better authentication

That sequence keeps the app easy to adopt while making it much easier to hand over to IT.
