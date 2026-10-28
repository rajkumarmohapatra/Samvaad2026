# Phase and acceptance status

Status as of 2026-10-28. “Local tested” means Python domain tests, not Microsoft production acceptance.

| Phase | Available artifacts/behavior | Remaining blocker and next priority |
|---|---|---|
| 0 Feasibility | Environment inspection, architecture comparison, license checklist, privacy/security design | Tenant SKU, policy, owner and identity confirmation; decision remains conditional |
| 1 Core | Functional local workbench; 3,000 current + 600 historical synthetic participations; Excel/CSV templates; stream-scoped domain permissions; import preview/commit; basic approvals; full-count dashboard; SharePoint core provisioning script and Power Fx recipes | Native canvas app, import/master resolver and snapshot/promotion flows need tenant construction and validation. Provisioning script unexecuted |
| 2 Arrival/registration | Local independent arrival/registration, bed exclusivity/accessibility, trip capacity and kit duplicate rules; audit timelines | Native UI/flows, eligibility/identity checklist, future reservations, full restrictions, QR/badges/reprints not completed |
| 3 Full operations | Local meal capacity/duplicate rules and finance maker/checker/payer methods; logical schemas for transport, food, sessions and incidents | Full schedules, entitlements, cancellations, bank vault, finance UI, reconciliation, incident workflows and native modules not built |
| 4 Participant access | Secure architecture option and organizer-assisted procedure | No self-service portal, contact mapping or external identity configuration |
| 5 Reporting | Synthetic star export, Power Query and DAX sources, page/RLS specifications | Desktop model creation, tenant refresh, all operational facts, RLS testing and publication incomplete |
| 6 Hardening | 36 local tests including 6,000 current + 600 historical scale dataset and concurrent last-bed test | Browser rendering unverified; sandbox socket launch interrupted. No Entra/SharePoint negative tests, flow chaos testing, accessibility audit, UAT or load certification |

No phase is declared operationally complete. The first tenant priority is a **one-stream synthetic pilot**: provision secured lists, build/save/publish the canvas app, configure versioned snapshot + review + promotion flows, then run backend permission tests with distinct accounts. Do not load real identity/bank/health data.

Acceptance criteria 1–18 are not signed off. Local evidence covers parts of 1–4, 5–7, 9–11, 13–16. Criteria 8 (badges), 12 (production permission paths), 17 (staff walkthrough) and 18 (confirmed licensing) remain explicit blockers. A local working prototype does not fulfill the full production brief.

File inventory: `README.md`; architecture feasibility/ERD; requirements status/invariants; data-model dictionary/JSON/seeds; SharePoint script/core schema; Power Fx/Studio build guide; workflow specs/build/expressions; Power BI exporter/queries/measures/report model; permission matrix/governance; deployment runbook; Excel/CSV templates and generator; local API/UI/domain engine; automated tests and manual UAT; user guides. Consult each folder for the exact generated files.
