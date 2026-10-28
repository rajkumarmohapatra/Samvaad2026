# Samvaad 360 standalone portal

This is the native web portal requested after the original Microsoft-first brief. It uses Django 5.2, server-rendered responsive screens, Django authentication, server-enforced role/edition/stream checks, and PostgreSQL for hosting. Microsoft 365 is not required. The older `workbench/` is a local test tool and must not be deployed.

## Run locally with synthetic data

From the repository root:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r portal/requirements.lock
cd portal
DEBUG=true ../.venv/bin/python manage.py migrate
DEBUG=true ../.venv/bin/python manage.py bootstrap_portal --demo --count 3000
DEBUG=true ../.venv/bin/python manage.py createsuperuser
DEBUG=true ../.venv/bin/python manage.py runserver 127.0.0.1:8000
```

Open http://127.0.0.1:8000. `--demo` refuses to run in a non-empty portal. It creates 3,000 current-year and 600 historical participations; no shared or default login passwords are seeded. Exact initial organisational names are retained. Four streams are classified only within the synthetic demo setup, not as a governance assertion.

Do not expose Django runserver or DEBUG=true publicly. Development uses local SQLite; production must use persistent PostgreSQL. SQLite test results do not prove PostgreSQL concurrency behavior.

## Supported operational paths in this source

- Event editions, immutable yearly name/state/stream snapshots, multiple roles and scoped permissions; privileged administrative setup.
- Participant draft creation/editing, duplicate review warnings, submission, separate reviewer decision, identity status, independent arrival/registration/departure and timeline.
- CSV/XLSX preview and row errors, server-session-staged commit and retry-safe saved rows.
- Dated accommodation reservations, accessibility/configured compatibility, overlap and room capacity checks, check-in/check-out/cancellation.
- Vehicles, travel plans, trips, passenger allocation and trip capacity checks.
- Food locations/windows, entitlements and one-time meal recording inside the service window.
- Kit inventory, ordinary issuance, one linked replacement and stock safeguards.
- Venues/sessions, capacity-limited assignment and attendance.
- Restricted encrypted bank record entry, masked bank review, separate bank verifier, claim maker/checker/payer, external reference/failure/reconciliation tracking. The application never transfers money. Full account numbers are not returned to ordinary views.
- Printable badges with locally generated opaque QR tokens and replacement revocation; authenticated staff lookup. Browser printing/PDF saving is manual, not unattended PDF delivery. No camera scanning UI is included; use a scanner that inputs the opaque token into search.
- Helpdesk ownership/priority/status and restricted safety/finance case visibility.
- Live operational counts and protected aggregate CSV export; historical edition totals.
- Authenticated participant-only itinerary, linked by the administrator after identity verification. No public self-claim based on a guessable participant ID.

## What is not certified or complete

This remains a pilot until deployed and accepted. It is not a claim that the complete original enterprise brief is fulfilled. Scheduled email/SMS notifications, automatic escalation delivery, password-reset email, external SSO/MFA, translation packs, attachment/identity-document upload, arbitrary custom workflow stages, formal archival/deletion jobs, bank integrations, automated backups, full financial/year-on-year analytical charts and production browser/load/concurrency validation remain rollout work. Account recovery is administrator-operated. Staff provisioning and profile linkage are privileged Django administration tasks.

A room change is currently checkout/cancel followed by a new allocation, each audited; no single-step atomic move UI. Trip cancellations and vehicle schedule reconciliation require further workflow hardening. Master reuse is administrator-controlled; a new-year nomination can explicitly link an existing participant. Do not change a participant master to rewrite annual snapshots.

The native portal uses server-side role grants for export. A readable screen can still be manually copied; this is not digital-rights-management. Community is not included in general analytics. Geographic reporting remains identifiable/pseudonymous information and requires privacy review.

## Administration

Create Event, Edition, Unit/EditionUnit, users, Membership and RolePermission in `/admin/` with a superadministrator. Ordinary staff, even if `is_staff` is set, cannot enter this administrator console. Default grants install via `bootstrap_portal`; do not rerun policy seeding as a substitute for a planned permission change.

Give every staff user an active edition membership. StreamOwner needs a specific stream; a null-stream StreamOwner does not receive global access. Default role IDs are listed in `operations/access.py`. Link a verified participant to its user in the Participant administrator form for `/my-visit/` access. No member can claim another profile by changing a URL.

Bank encryption requires a stable Fernet key in `FIELD_ENCRYPTION_KEY`. Store and back it up in an approved secret manager; losing it prevents decryption. Key rotation/approved bank verification processes must be designed before real finance use. Bank capture is disabled when the key is missing. Tokens, passwords, plaintext bank records and participant data must never enter GitHub or logs.

## Deploy from GitHub

GitHub holds the source. GitHub Pages cannot run this Django backend. Deploy `portal/` as one Python web service on a host such as Render and attach a persistent Postgres database (for example a separate Neon project).

Build command: `bash build.sh`

Start command: `bash start.sh`

Health check: `/healthz`

Set Python 3.12, SECRET_KEY, DATABASE_URL (pooled), DATABASE_URL_UNPOOLED (direct for migrations), ALLOWED_HOSTS/CSRF origins and optional FIELD_ENCRYPTION_KEY/BOOTSTRAP_TOKEN in the host secret store. The app learns Render's own hostname from RENDER_EXTERNAL_HOSTNAME. Configure no wildcard production hosts, no DEBUG=true and no fallback ephemeral SQLite. The settings fail closed if SECRET_KEY is missing; a production PostgreSQL requirement is also enforced.

The source includes one-time `/setup/` for the first superadministrator only when BOOTSTRAP_TOKEN is configured; supply that code privately through the hosting secret store, choose a personal strong password in the form, and remove the setup token after use. The endpoint stops accepting setup once a superadministrator exists. Alternatively use the host's private console with `python manage.py createsuperuser`.

Only one migration runner is supported by the included start script. For multiple service instances use an approved single pre-deployment migration job with a direct Postgres connection, rather than starting migrations concurrently. The service uses transactional per-edition row locks for capacity operations; validate behavior on Postgres before event use. A free/sleeping compute plan is suitable only for evaluation, not a reliability promise for event-day operations. Verify cost, plan limits, backups, data residency and retention before production.

## Tests

```bash
cd portal
TESTING=1 ../.venv/bin/python manage.py test operations
```

TESTING enables a fast test-only password hasher; it must not be set on a public deployment. Live sign-in uses Django's production password hashers. Test fixtures are synthetic.
