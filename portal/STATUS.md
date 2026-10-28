# Native portal status

This supersedes the original Microsoft-first architecture for the requested standalone web portal. Microsoft deployment files remain in the repository as reference deliverables.

## Verified locally

- Django system checks and initial schema migration.
- 62 server/authentication/permission/domain/template/dashboard/notification tests.
- Actual generation of 3,000 current-year and 600 historical synthetic participations in the local development database.
- Original 36 standalone domain/artifact tests remain a separate validation suite.

## Not yet verified

- The owner reports successful administrator access. An automated authenticated live-browser walkthrough remains outstanding. Render deployment and unauthenticated HTTP routes have been verified live.
- PostgreSQL concurrency/fault tests. The per-edition transaction locks require PostgreSQL in production; SQLite does not prove those row-lock guarantees.
- End-to-end browser accessibility, peak-user performance, production backup/restore and privacy acceptance.
- Complete original enterprise scope: see README limitations, including notifications, escalation delivery, reset email/SSO/MFA, uploads, formal retention jobs, full analytics and operational edge-case workflows.

Do not describe the repository as a live, complete production platform. Rollout status and hosting URL must be updated only after actual deployment verification.

## Workbook-aligned dashboard and notifications

Adds field coverage documented in `docs/WORKBOOK-FIELD-MAPPING.md`, server-filtered chart/table dashboard, restricted identity-type capture, and searchable persisted notifications. Raw attached workbooks/PDFs and personal source rows are not in this public repository. Pageview tracking starts with this release; historical audit actions are migrated with their original timestamps. Browser rendering/accessibility remains to be verified separately.
