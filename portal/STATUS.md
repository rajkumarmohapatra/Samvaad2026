# Native portal status

This supersedes the original Microsoft-first architecture for the requested standalone web portal. Microsoft deployment files remain in the repository as reference deliverables.

## Verified locally

- Django system checks and initial schema migration.
- 35 server/authentication/permission/domain/template tests.
- Actual generation of 3,000 current-year and 600 historical synthetic participations in the local development database.
- Original 36 standalone domain/artifact tests remain a separate validation suite.

## Not yet verified

- Live host deployment, account setup and live browser operation.
- PostgreSQL concurrency/fault tests. The per-edition transaction locks require PostgreSQL in production; SQLite does not prove those row-lock guarantees.
- End-to-end browser accessibility, peak-user performance, production backup/restore and privacy acceptance.
- Complete original enterprise scope: see README limitations, including notifications, escalation delivery, reset email/SSO/MFA, uploads, formal retention jobs, full analytics and operational edge-case workflows.

Do not describe the repository as a live, complete production platform. Rollout status and hosting URL must be updated only after actual deployment verification.
