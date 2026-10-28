# SAMBAD 360

A Microsoft-first implementation foundation and an executable **local synthetic acceptance workbench**. This repository is not yet a production-ready Power Platform solution. No tenant deployment has occurred.

## Step-by-step setup and copyable instructions

- [Read the setup workbook](user-guides/SAMBAD-360-Step-by-Step-Setup.md)
- [Download the editable Word guide](user-guides/SAMBAD-360-Step-by-Step-Setup.docx)
- [Download the PDF guide](user-guides/SAMBAD-360-Step-by-Step-Setup.pdf)
- [Copy-and-paste snippets](user-guides/setup-copy-pack/README.txt) and [snippet index](user-guides/setup-copy-pack/INDEX.json)

The workbook covers SharePoint columns and permissions, a three-screen draft-entry canvas app, developer requirements for protected approvals, Power BI measures, and pilot tests. Power Apps formulas and workflow specifications still require compilation, configuration, and validation in the intended Microsoft tenant.

## Open the local working version

Requires Python 3.12 or later. Runtime and tests use the standard library; Excel template regeneration optionally needs openpyxl.

```bash
git clone https://github.com/rajkumarmohapatra/Samvaad2026.git sambad-360
cd sambad-360
python3 tools/seed.py --db test-data/generated/my-pilot.db
python3 -m workbench.server --db test-data/generated/my-pilot.db
```

Open **http://127.0.0.1:8765** on the same machine. Use a new database filename when seeding; existing databases are never overwritten. The pre-generated `test-data/generated/synthetic.db` can also be opened using `python3 -m workbench.server`.

The server binds only to loopback. It deliberately allows local test-persona switching and is **not production authentication**. Do not expose it through a tunnel, deploy it externally, or enter real data. A sandbox may deny listening sockets; run the commands on an authorized local development computer in that case.

Working local behaviors: event/unit creation, stream-scoped nominations, drafts and submission, reviewer approval/rejection, name/ID/phone/token search, independent arrival/registration/departure states, paginated directory and dashboard, CSV preview/import with row errors, participant timeline, bed check-in/out, trip allocation, kit and meal issuance. Finance maker/checker/payer rules and unit changes are executable through the domain API and tested; there is no finance UI. Safety cases, full travel schedules, badge scanning, eligibility rules, session attendance, alerts, replacements and localization are not implemented.

The local accommodation rules cover edition, accessibility and exclusive active beds only; they do not yet implement future-date reservations or all compatibility/eligibility policies. Local food/kit rules check active registration, capacity and duplicate issuance, not full entitlement policy. Do not interpret local test results as operational acceptance.

## Microsoft rollout

Start with [deployment/DEPLOY.md](deployment/DEPLOY.md), [architecture/feasibility.md](architecture/feasibility.md) and [requirements/STATUS.md](requirements/STATUS.md).

- `sharepoint/Provision-Core.ps1`: real PnP PowerShell script for empty, permission-isolated core lists; not executed or PowerShell-validated here.
- `power-apps/Core.fx`: property-level Power Fx formulas and Studio instructions, **not an importable app**.
- `power-automate/`: workflow specifications, expressions and construction/recovery instructions, **not exported/importable flows**.
- `power-bi/`: synthetic data export, Power Query, DAX, star-model/report/RLS instructions; **not a PBIP/PBIX or published dataset**.
- `data-model/`: 50 logical entity definitions and dictionary; only the core subset has a provisioning script. All 40 initial names are preserved exactly and initially unclassified.
- `security/`: permission matrix and enforcement/governance limitations.
- `test-data/`: Excel/CSV templates and synthetic generator.

## Run tests

```bash
python3 -m unittest discover -s tests -v
node --check workbench/static/app.js
python3 tools/export_analytics.py --db test-data/generated/synthetic.db --out power-bi/sample-data
```

Microsoft-only hosting remains the recommended production route. SQLite and the workbench are development artifacts, not a proposed externally hosted replacement.
