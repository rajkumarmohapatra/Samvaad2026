# Samvaad 360

A standalone event operations portal for the participant journey at Samvaad. **The requested web version is no longer Microsoft-first:** it uses Django, authenticated staff/participant accounts, server-side role and stream permissions, and PostgreSQL for persistent hosting.

## Start here

- [Native web portal: run, configure and deploy](portal/README.md)
- [Native implementation and verification status](portal/STATUS.md)
- [Native application source](portal/operations/)
- [Original Microsoft 365 step-by-step workbook](user-guides/SAMBAD-360-Step-by-Step-Setup.md)
- [Word setup guide](user-guides/SAMBAD-360-Step-by-Step-Setup.docx) · [PDF setup guide](user-guides/SAMBAD-360-Step-by-Step-Setup.pdf)
- [Copyable Microsoft setup snippets](user-guides/setup-copy-pack/INDEX.json)

The Microsoft guides describe the earlier architecture. They are retained for reference and do not deploy or configure the native portal.

## What the native source supports

Participant nominations and versioned journey changes; CSV/XLSX validation/import; approvals and identity status; independent arrival/registration; dated bed reservations/check-in/check-out; vehicle/trip capacity; food entitlements/meal recording; kit stock and replacements; sessions/attendance; restricted finance approvals and external payment recording; encrypted bank storage; printable opaque QR badges; helpdesk/sensitive cases; protected aggregate reports; administrator-linked participant-only itineraries.

**Pilot source, not a production-completeness claim.** The native suite has 35 local tests. The earlier domain/artifact suite has 36 local tests. Hosted PostgreSQL concurrency, live browser operation, backup/restore, full privacy review and the remaining enterprise features are not yet accepted. See the native README for explicit limitations. Nothing here transfers money or authenticates someone using only a badge token.

## Local native development

```bash
git clone https://github.com/rajkumarmohapatra/Samvaad2026.git
cd Samvaad2026
python3 -m venv .venv
.venv/bin/python -m pip install -r portal/requirements.lock
cd portal
DEBUG=true ../.venv/bin/python manage.py migrate
DEBUG=true ../.venv/bin/python manage.py bootstrap_portal --demo --count 3000
DEBUG=true ../.venv/bin/python manage.py createsuperuser
DEBUG=true ../.venv/bin/python manage.py runserver 127.0.0.1:8000
```

Use a fresh local database for `--demo`; the generator refuses a non-empty portal. On Windows use `.venv\Scripts\python.exe` and set environment variables using PowerShell syntax. No default/shared administrator passwords are seeded.

## Hosting

GitHub stores and reviews the source. GitHub Pages serves static files and **cannot run this application's secure Django backend**. A connected full-stack host runs `portal/` and a persistent PostgreSQL database stores the records. Host choice, account destination and any paid plan must be confirmed. Do not host the old `workbench/` as a public service.

Secrets belong in the host's secret store. Never commit real participants, contact/identity/bank/health data, `.env`, database files, bootstrap codes or access tokens. The repository includes synthetic sample reporting CSVs only. Use HTTPS, production settings, least privilege and tested backup/retention controls before real event use.

## Repository map

| Folder | Contents |
|---|---|
| `portal/` | Native Django portal, schema migration, tests and host commands |
| `architecture/`, `requirements/`, `data-model/` | Original requirements, architecture and logical dictionary |
| `sharepoint/`, `power-apps/`, `power-automate/`, `power-bi/` | Earlier Microsoft-first source artifacts and samples |
| `security/`, `deployment/`, `user-guides/` | Governance, deployment references and setup workbook |
| `workbench/`, `tests/`, `tools/` | Original local synthetic acceptance workbench and artifact generators |

The workbench intentionally permits local test-persona switching and is not a production authentication system. The native portal uses real authenticated accounts and backend permissions instead.
