from pathlib import Path
R=Path(__file__).resolve().parents[1]
files={
'README.md':'''# SAMBAD 360

A Microsoft-first implementation foundation and an executable **local synthetic acceptance workbench**. This repository is not yet a production-ready Power Platform solution. No tenant deployment has occurred.

## Open the local working version

Requires Python 3.12 or later. Runtime and tests use the standard library; Excel template regeneration optionally needs openpyxl.

```bash
cd /workspace/sambad-360
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
''',
'architecture/feasibility.md':'''# Feasibility and architecture decision — 2026-10-28

**Recommend Option A for a controlled internal pilot, conditionally on confirmed entitlements and tenant security tests. Recommend Option B for the complete high-concurrency platform if premium funding is available. Neither is deployed.**

Observed: Python 3.12.14, Node 24.19.0 and npm are available. PowerShell, pac, az and dotnet were absent. No configured Microsoft outbound identity or secrets. The connected SharePoint tool exposes document operations, not the list provisioning/Power Apps/flow lifecycle APIs needed for deployment. Microsoft Learn URLs below returned HTTP 200 on 2026-10-27. Tenant-specific licensing remains unverified.

| Concern | A: canvas + SharePoint + standard flows | B: canvas + Dataverse + flows + optional Power Pages |
|---|---|---|
| License | May fit selected Microsoft 365 seeded rights for standard connectors; plan and usage verification required | Premium app/automation and capacity entitlements generally needed; verify contract |
| Backend security | List/site boundaries; no field security. Stream partition lists and service-owned projections. Read access permits extraction | Security roles, record ownership/team access, column security; deliberate configuration still required |
| Concurrency | No multi-list transaction. Requires one protected command dispatcher, unique receipt keys, ETags and reconciliation | Server-side transactions/custom API for critical allocations; client checks alone insufficient |
| 3,000/year | Feasible with indexed selective queries, paging and yearly partitions. Native canvas counts/search require care | Stronger relational querying and security model for larger history |
| Maintenance | Low infrastructure cost, significant partition/app/flow maintenance; 40 separate stream apps are not a desirable final design | More upfront engineering/licensing; simpler relational governance and solution ALM |
| External access | No anonymous canvas access. Entra B2B guests need suitable app entitlements and explicit backend access; unsuitable as assumed participant portal | Power Pages authenticated per-contact access with table permissions, Dataverse and separately confirmed capacity |
| Reporting | SharePoint refresh is import-based; viewer licensing and refresh limits require confirmation | Similar Power BI sharing/licensing checks; Dataverse access alone does not grant report access |

Architecture: Entra internal users → signed-in-user canvas connections → stream-specific nominations. Service-owned flows snapshot submissions into reviewer-only queue, then publish minimal read-only team projections. Restricted profile, identity, finance and safety sites remain separate. Banking collection is **disabled** until a dedicated vault boundary, retention and access controls are validated. A shared list with hidden columns cannot protect banking fields.

A stream owner's editable nomination is not an approved record. Approval uses the versioned snapshot reviewed by an authorized reviewer; later source edits require a fresh review. Annual snapshots preserve labels and facts while reusable participant masters persist separately. The local model supports historical reuse but the tenant master-resolution workflow is unfinished.

Accommodation, trips and stock need protected service writes, not canvas Patch directly to inventory. A single serialized dispatcher plus reconciliation can reduce SharePoint races; this remains to be built and load-tested. Do not operate these modules under concurrency until it is proven. If acceptable recovery/throughput cannot be achieved within standard connectors, obtain approval for Dataverse and server-side transactional logic. No external host is proposed.

Participant access in the first release: organizer-operated information view after identity verification, showing only approved itinerary details. The participant must not receive the organizer account, internal list URL or access to the shared app. Self-service option: Power Pages with a supported Entra External ID or other approved identity provider and contact-scoped table permissions; not implemented or assumed licensed. A random badge token is a lookup aid, not authentication.

Licensing checklist before purchasing/building: exact Microsoft 365 SKU; Power Apps standard-connector rights for every internal/guest user; automation ownership and request limits; DLP; service-account policy; Power BI Pro/PPU or qualifying capacity for all viewers; refresh limits; desktop Office/Word if used for badge printing; PDF conversion connector entitlements; Power Pages authenticated-user capacity; Dataverse database/file/log capacity; premium custom connectors and Managed Environment implications. Record outcomes, owner and date in the deployment signoff.

References verified as reachable, not as tenant entitlement evidence:
- https://learn.microsoft.com/en-us/power-platform/admin/powerapps-flow-licensing-faq
- https://learn.microsoft.com/en-us/power-apps/maker/canvas-apps/delegation-overview
- https://learn.microsoft.com/en-us/power-apps/maker/canvas-apps/connections/connection-sharepoint-online
- https://learn.microsoft.com/en-us/power-apps/maker/canvas-apps/power-apps-yaml
- https://learn.microsoft.com/en-us/power-pages/security/authentication/

SharePoint performance controls: index EditionId, StreamId, FullName, Phone, RecordKey and relevant status/time columns before loading. Phone needs an index added to the core nominations list during tenant setup. Use one selective indexed first filter; indexes do not make every OR query threshold-safe. Lists can exceed 5,000 items, but a threshold-breaking query can still fail. Do not fix delegation by raising the client row cap to 2,000. Avoid Lower, in-memory joins, Distinct and client CountRows over SharePoint. Prefix and exact-search modes should be separate and tested with records beyond row 5,000. Use paginated scheduled extraction and incremental watermarks with overlap/deduplication; preserve a recorded refresh timestamp. Protect against SharePoint throttling with Retry-After and bounded retries. Archive by edition without breaking immutable identifiers and reports.
''',
'architecture/model.mmd':'''erDiagram
  Events ||--o{ EventEditions : has
  EventEditions ||--o{ EditionUnits : configures
  OrganizationalUnits ||--o{ EditionUnits : classified_by_edition
  Participants ||--o{ EventParticipations : attends
  EventEditions ||--o{ EventParticipations : includes
  EventParticipations ||--o{ ParticipantStreamAssignments : has
  OrganizationalUnits ||--o{ ParticipantStreamAssignments : stream
  EventParticipations ||--o{ ParticipationSnapshots : preserves
  EventParticipations ||--o{ TravelBookings : travels
  Vehicles ||--o{ Trips : operates
  Trips ||--o{ TripPassengers : carries
  EventParticipations ||--o{ TripPassengers : assigned
  AccommodationProperties ||--o{ Buildings : has
  Buildings ||--o{ Rooms : has
  Rooms ||--o{ Beds : contains
  Beds ||--o{ AccommodationAllocations : reserves
  EventParticipations ||--o{ AccommodationAllocations : stays
  MealLocations ||--o{ MealWindows : serves
  MealWindows ||--o{ MealTransactions : records
  EventParticipations ||--o{ MealTransactions : consumes
  EventParticipations ||--o{ KitIssues : receives
  Participants ||--o{ RestrictedBankDetails : secured_separately
  EventParticipations ||--o{ IdentityVerification : verified
  EventParticipations ||--o{ FinancialRequests : requests
  FinancialRequests ||--o{ FinancialApprovals : checked
  FinancialRequests ||--o{ PaymentRecords : external_payment
  Venues ||--o{ ActivityLocations : contains
  ActivityLocations ||--o{ Sessions : hosts
  Sessions ||--o{ SessionAssignments : attends
  EventParticipations ||--o{ SessionAssignments : participates
  EventParticipations ||--o{ HelpdeskTickets : requests_help
  EventParticipations ||--o{ ApprovalHistory : audited
''',
'requirements/invariants.md':'''# Rules and release gates

1. A participant master and annual participation have separate keys. Unique (participant, edition); UUID participation and badge references. Exact name+phone creates a duplicate-review warning, never an inferred identity/community merge. Shared family phones remain possible.
2. Stream permissions must apply at the backend. Multiple roles are additive only within authorized scope; administrator access is privileged and monitored. The local harness has roles and stream scopes but not production edition-scoped Entra authorization.
3. Review, travel, arrival, accommodation, registration, kit, finance and departure are independent state machines. Registration does not depend on a bed. Required identity/eligibility checks remain tenant/module release gates.
4. Every accepted transition needs actor, UTC timestamp, immutable audit, expected version and retry key. Reject stale writes. An idempotency key cannot be reused for different input. Retry failed operations without duplicate service issuance.
5. Active beds are exclusive. Full solution must also enforce date-range overlap, configured compatibility, eligibility, accessible inventory and room capacity. The local harness tests exclusive active allocation and optional accessibility only.
6. Vehicle capacity is checked atomically, including cancellations and vehicle changes in the final module. Full implementation must prevent overlapping trips for a vehicle/driver. Current harness supports per-trip capacity only.
7. Meal serving and ordinary kit issue have unique participation/service keys; no negative stock. Entitlements, replacements and reconciliation must be added before rollout.
8. Money uses integer paise; maker, checker and payer are different people. App records an external payment reference only. No bank transfer is performed. Bank verification/approval limits/reprocessing remain unfinished.
9. Closed editions reject operational writes. Historical labels and participation details are snapshots, not dynamically overwritten master fields.
10. Export authorization is not enforceable merely by hiding Export. Readable SharePoint records can be retrieved through APIs. If the owner requires a strict separate export right, Option A does not fully satisfy it; escalate the architecture and device/session controls.
11. No banking/identity/contact data in QR, logs or analytics. Community analysis requires authorized purpose, access restrictions and small-cell suppression. Never infer tribal identity.
12. Approval/commands must authorize SharePoint Created By against server-configured groups and scope. Never accept caller-supplied email, role, approver or stream as evidence of authority.
''',
'requirements/STATUS.md':'''# Phase and acceptance status

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
''',
'security/GOVERNANCE.md':'''# Security and privacy boundary

**Never authorize through hidden UI controls alone.** The role matrix is a target policy, not proof of deployed grants. All cells omitted from it are denied by default. `export=false` is a policy intent; SharePoint Read permits extraction and cannot implement a distinct export deny. All deletion is withheld from ordinary users; privileged records administrators follow approved retention/hold processes.

Create a dedicated private pilot site with owners only and no Microsoft 365 group membership granting broad access. Use Entra groups/site groups, MFA and conditional access where licensed. Only a few privileged owners may configure permissions. Disable external/anonymous sharing at tenant/site level as approved, and disallow member sharing. Check direct user grants and sharing links as well as group membership.

Stream drafts use separate lists. Ordinary owners cannot read another partition through REST, search or Excel connections. ReviewQueue is reviewer-only plus the automation identity; do not expose raw queue snapshots to registration/analytics. Reviewers can edit review rows in the pilot and are trusted for approval; stronger separation/version-bound decisions require the protected command/approval workflow before production. Configuration role matrices cannot dynamically enforce SharePoint rights: an administrator must apply and test underlying grants when roles change.

Team projections contain only the minimum data needed by that team. Finance/identity/safety must not be columns in a shared operational list. Implement separate restricted sites/libraries with unique permissions, no anonymous links, no broad navigation/search exposure, and only the authorized service identity for cross-boundary processing. Site owners/tenant administrators remain privileged, not technically excluded by ordinary list ACLs.

Full banking collection is disabled in this build. Prefer verification with an approved finance system and a masked reference in SAMBAD. If full details are justified, require approved vault design, need-to-know finance groups, sensitive input/output controls, no general exports, and a tested retention mechanism before enabling. Identity copies are not needed merely to track “verified”; keep only status and authorized verifier unless purpose demands a document. Restricted safety cases must never be entered in an ordinary helpdesk summary.

Power Automate service account: dedicated, least privilege, connection references stored in the environment, restricted flow ownership. No flow Run endpoint that lets a caller impersonate an approver. Authorize command Created By, verify immutable list scope, whitelist fields, pin reviewed source version, and never trust client-supplied role/email. Enable Secure Inputs/Outputs for sensitive actions, limit run-history access and avoid PII in error notifications. Service audit list append-only (admins still privileged). SharePoint versioning is not immutable compliance storage; require approved retention/audit capabilities where licensed.

Privacy owner must review the Indian Digital Personal Data Protection Act and the applicable rules/commencement dates, sector requirements and contractual obligations with counsel. This package is not a legal compliance certification. Record purposes, lawful basis/notice, optional data handling, grievance contact, processors, access requests, correction/deletion process and incident escalation. Do not assume consent alone resolves all processing. Collect age/gender/health only for approved operational necessity; age/children safeguards need review if minors participate. Preserve self-described tribal affiliation with no forced taxonomy or inference.

Retention is policy-driven, not an arbitrary universal duration. Each entity lists a proposed review point. Approve concrete deletion dates, legal holds, backup handling and evidence before loading production data. After each event, review access, expire temporary memberships, remove unneeded documents, reduce identifiable analytics, and retain protected finance/audit evidence only under the approved schedule. Test deletion across lists, libraries, flow history and exports.

Backup/recovery: define target RPO/RTO with the event director; versioning/recycle bin alone is not backup. Arrange a licensed Microsoft 365 backup or approved protected export with encryption, access logging and retention. Take configuration/solution exports before changes. Conduct a restore rehearsal to a restricted pilot; reconcile authoritative request receipts and allocations before resuming. Keep a numbered, access-controlled offline desk procedure during outages; reconcile each operation once, rather than replaying loose spreadsheets.

Incident response: stop affected flows, preserve protected audit evidence, revoke compromised sessions/grants, notify designated incident/privacy owners under the approved response timetable, assess disclosure obligations, restore safely and document reconciliation. Do not put incident details in broad Teams/email channels.
''',
'deployment/DEPLOY.md':'''# Deploy and open a Microsoft pilot

This runbook creates a **pilot foundation**, not an automatic full deployment. No step has been performed against your tenant. A Microsoft 365/Power Platform administrator must perform authenticated steps; do not send passwords, tokens or real participant data to the coding assistant.

1. Choose the tenant, private SharePoint pilot site, Power Platform environment and named administrator. Confirm the license checklist in `architecture/feasibility.md`. Record approvals and the privacy/records owner. Do not assume premium rights.
2. On the administrator's computer install current supported PowerShell 7 and PnP.PowerShell. Check PnP's current PowerShell requirement before selecting a version. The script's minimum version is not a guarantee that every future PnP release supports that version. Use `Install-Module PnP.PowerShell -Scope CurrentUser`, then inspect the installed version and help. PnP is a community-supported Microsoft 365 administration tool; tenant admins approve its use.
3. Register/approve an Entra application for PnP delegated interactive login using your organization's approved procedure and consented SharePoint scopes. Supply its real client ID. No legacy ACS app-only credential or shared client ID is used. Do not grant tenant-wide privileges merely to bypass a site error.
4. Create a dedicated private SharePoint site. Restrict its site-wide role assignments to the owners group only. Remove the default Members/Visitors **site grants**, not just their memberships, and check sharing/site admin policy. The script deliberately refuses any other site-wide role assignment. This is a strict pilot precondition.
5. Copy `streams.example.json` to your own configuration file. Replace the example with one or more approved stream classifications and stable uppercase alphanumeric codes. Initial supplied organizational names have not been classified for you. Start with one pilot stream.
6. Review the script and run a dry run, replacing the sample URL and GUID on your own computer:

```powershell
./sharepoint/Provision-Core.ps1 -SiteUrl 'https://YOURTENANT.sharepoint.com/sites/SambadPilot' -ClientId 'YOUR-ENTRA-APP-GUID' -StreamConfiguration './deployment/streams.pilot.json' -PrivateSiteVerified -WhatIf
```

Then rerun without `-WhatIf`. It creates empty lists and groups; it does not create sites, add users, upload data, provision vaults or install apps/flows. Existing lists are skipped with a warning, not migrated or certified. An interrupted run requires an admin to inspect ACLs/schema before retrying; no automatic rollback is claimed.

7. Add distinct test users to `SB Config Readers`, the relevant `SB Stream <CODE>`, `SB Reviewers`, and `SB Registration Readers`. Add only the dedicated workflow account to `SB Automation`. Add owners/stream users to Config Readers as appropriate. Do not add stream users to automation, reviewer or site owner groups. Use actual role combinations only after least-privilege tests.
8. Add a Phone index to each nominations list and a FullName index; confirm all schema indexes. Create one event, edition, unit and edition-unit mapping using GUID keys and UTC timestamps in Lists. Source seed JSON contains organizational names only; initial event records need admin creation. Required application GUID/date fields are supplied by canvas forms or explicit admin entry. These are not preconfigured native list forms.
9. In https://make.powerapps.com create the canvas apps using `power-apps/BUILD.md`. The supplied formulas are property snippets. Complete the listed screen/control and validation setup. Save and run App Checker.
10. In https://make.powerautomate.com create the snapshot/review/promotion workflows using `power-automate/BUILD.md`. Definitions in this repository are specifications, not an importable ZIP. Restrict the automation connection and use server-side authorization; no workflow is installed by this package.
11. Use **synthetic data only** for the first pilot. The local Excel/CSV import works only in the workbench; native bulk import/master resolution is unfinished. Load a handful of synthetic nominations via the canvas form, submit, review and verify read-only projections. Then run the full tenant tests including >5,000 rows in one test partition.
12. Create the Power BI model in Desktop using `power-bi/BUILD.md`. Publish only after validating RLS, viewer roles, sharing, export and refresh permissions. Do not use Publish to web.
13. Share each published canvas app with its matching test group. Give the staff the app's actual **Play** URL from Power Apps, or add that app to an approved SharePoint page. Verify a member can sign in through Entra and a nonmember cannot access underlying lists/APIs. A local workbench URL does not open Power Apps.
14. Run `tests/TENANT-UAT.md` and the staff guide. Record actual URLs, owner, version, license decisions, test evidence and unresolved blockers. No real-data go-live until the project owner signs off all applicable acceptance criteria.

Full rollout next: complete native participant/master resolver, signed-off import, protected transactional command processing, operational projections/modules, restricted vault, external access option and complete reports. If SharePoint concurrency/security compromises fail acceptance, move to licensed Dataverse; do not silently weaken requirements.
''',
'power-automate/BUILD.md':'''# Workflow construction — not installed/importable

No fabricated exported flow or connection reference is included. `workflows.json` is an implementation specification, **not** an importable Power Automate package. Exact action bindings, connections, list GUIDs and server permissions require tenant access and designer validation. Local domain tests do not test these flows.

## Core pilot: snapshot, review, promotion

1. Use the standard SharePoint connector and a dedicated service identity. Create a solution if your confirmed environment supports it; use connection references/environment variables. Avoid assuming Dataverse solution storage is licensed. Otherwise document environment-specific settings and export the created flows from the designer after validation.
2. Per stream, create an automated flow triggered by “When an item is created or modified” on its **fixed** nominations list. Trigger condition: `@equals(triggerBody()?['SubmitRequested'], true)`. Set trigger concurrency to 1. Bind the authoritative stream and edition allowlist on the server, not from user-supplied fields. Get the item and version. Fetch its author/editor from SharePoint and validate membership/scope. Never infer identity from an input email.
3. Build a receipt key from fixed partition/list GUID, numeric item ID and **submitted source version**. NominationKey must identify that exact version, not just its ID. Check/create unique WorkflowReceipts.RequestKey. If create conflicts, retrieve the receipt and resume from its recorded stage. A unique key alone is not a completed workflow marker.
4. Whitelist name/contact/community fields needed by reviewers; validate lengths, formats, stream assignment and open edition. Do not copy health/bank/identity data. Create an immutable source snapshot in `SB_ReviewQueue` with NominationKey, SourceVersion, status `Submitted`, server-configured stream/edition and timestamps. Snapshot is reviewer-only. Record receipt.TargetId, then stage `SnapshotCreated`. If it already exists, confirm matching key/version and reuse it.
5. Reset SubmitRequested using an ETag conditional update, not unconditional overwrite. Treat a 412 conflict as “source changed”; retain the accepted snapshot and require the owner to submit a new version for later changes. Do not clear a newer submission. A production design needs explicit submission-command records to avoid ambiguous repeated flag edits; this remains a core release gate.
6. A separate reviewer-only app/List form edits only review decision, reason and timestamp. An automated review flow must validate the **editor's** actual SharePoint identity/group and decision against the exact snapshot/version. Reject self-approval where the approved policy requires it. Store actor/decision/source version in the protected audit. Rejected snapshots remain read-only to stream owners through a sanitized status projection; corrections create new versions.
7. Promotion uses the exact approved snapshot, not the current nomination. Before creating a reusable master, perform protected duplicate review and resolve cross-year identity explicitly. Create the canonical participation with a unique participant+edition constraint/key. Use a recoverable receipt for each write. Publish minimal stream and registration projections keyed by participation and source version. Do not publish raw Snapshot JSON. This tenant master/promotion logic is not implemented yet.
8. Finalize receipt only after canonical participation, projections and audit exist. A scheduled reconciler finds incomplete receipts and repairs/resumes each stage. Idempotent creation uses unique keys; ETag updates prevent stale writes. Never delete conflicting records to force success.

## Capacity-sensitive command dispatcher

Before native bed/trip/kit/meal rollout, provision append-only command lists per team/edition (not included in core script). Staff have create/read rights only to their permitted commands/projections, and no direct writes to authoritative inventory/allocations. A **single** scheduled dispatcher with concurrency 1 is the only writer across all capacity-changing operations; also turn off parallel Apply to each. Multiple independent concurrency-1 flows do not serialize one another.

For each command: identify immutable Created By → validate current server-side role/scope → compare expected source version → validate eligibility and all related edition IDs → reserve against current authoritative state → persist the unique request receipt and reservation → write ledger/audit → publish projections → mark completed. Use explicit Prepared/Reserved/Committed stages and reconcile partial failures before allowing capacity to be reused. No SharePoint multi-record atomic transaction is claimed. Do not go live without fault injection and load tests. If throughput or correctness cannot be proven, use licensed Dataverse transactional logic.

## Notifications, escalation and recovery

Use an outbox with unique request/stage/template/recipient key and no PII in subject lines. Email/send operations do not offer end-to-end exactly-once delivery: a crash after send but before marking sent may duplicate a notification. Do not promise duplicate-free notifications. Record delivery attempts; make approval/issuance state idempotent independent of notification retries. Escalate outstanding reviews after a configurable event-hours SLA to the authorized supervisor group; avoid broad recipient lists. Notify on final dead-letter failure and provide a protected retry procedure.

Use Try/Catch/Finally scopes and Configure run after for Failed/TimedOut/Skipped. Bounded exponential retries for 429/503 honoring Retry-After. Do not retry validation or permission failures as successful work. Redact outputs, enable Secure Inputs/Outputs where relevant and restrict flow run-history access. Dead-letter records contain correlation ID and error code, not private records. A finance disbursement flow never calls banking endpoints in this package.

After building in the tenant, test each workflow case in `tests/TENANT-UAT.md`, then export the genuine package/solution using the currently supported designer/CLI commands confirmed with `pac help`. No deprecated canvas pack/unpack or hand-made import ZIP is prescribed.
''',
'power-automate/expressions.md':'''# Designer expression snippets

These are expressions for named actions, not one importable definition. Verify dynamic content names in the tenant designer.

- Submission trigger condition: `@equals(triggerBody()?['SubmitRequested'], true)`
- Correlation: `workflow()?['run']?['name']`
- UTC timestamp: `utcNow()`
- UUID for a new server-side record: `guid()`
- Version-bound receipt: `concat(variables('PartitionListGuid'), ':', string(triggerBody()?['ID']), ':', string(body('Get_item')?['{VersionNumber}']))`
- Outbox key: `concat(variables('RequestKey'), ':', variables('Stage'), ':', variables('Template'), ':', variables('RecipientObjectId'))`

For SharePoint “Send an HTTP request to SharePoint”, an ETag update uses POST to `/_api/web/lists(guid'<LIST-GUID>')/items(<NUMERIC-ID>)`, headers `IF-MATCH: <ETAG FROM GET>`, `X-HTTP-Method: MERGE`, `Accept: application/json;odata=nometadata`, `Content-Type: application/json;odata=nometadata`. Body whitelists only the fields being updated. A stale ETag must return 412 and trigger re-read/conflict handling. Never use `IF-MATCH: *` for capacity or approvals. Insert actual IDs through safe designer parameters; no access tokens are embedded.

Group validation must query trusted group membership and compare the actual SharePoint author/editor identifier, not a client-supplied field. Nested Entra group membership may require capabilities beyond simple SharePoint group enumeration; verify your chosen group design and connector licensing. Fail closed on unresolved membership.
''',
'power-bi/BUILD.md':'''# Power BI model — source artifacts, not a PBIX/PBIP

No Desktop runtime or tenant access was available. The supplied exporter is executable; Power Query/DAX/model/page definitions require Desktop creation and validation. Synthetic report data is generated from the local database; it is not a production connector.

1. Run `python3 tools/export_analytics.py --db test-data/generated/synthetic.db --out power-bi/sample-data` from the repository root. The exporter accepts only a synthetic-seeded database and emits an explicit allowlist of pseudonymous fields. No name, contact, identity, bank or health fields are exported.
2. In Power BI Desktop create a blank report. Add a text parameter `DataFolder` pointing to the absolute sample-data folder. Create a function query `LoadCsv` with `LoadCsv.pq`, then load each CSV through `LoadCsv("FactParticipation.csv")` and the corresponding dimensions. Assign types from `model.json`. Apply single-direction 1-to-many dimension relationships; preserve the declared fact grains.
3. Create measures from `measures.dax` individually. Import `theme.json`. Build pages defined in `report-pages.json`. Default to a selected edition; show refresh timestamp and denominators. Keep finance on a separately permissioned report/model. Unimplemented operational facts must display “Not available”, never fake zero activity.
4. Production data source must be a service-produced analytics projection in SharePoint, not raw participant/finance vault lists. Configure SharePoint Online List connector with the approved URL, selecting only allowlisted columns. Scheduled paginated projection/extraction and refresh-health monitoring are still unimplemented. Do not let a dataset service account read the banking/document vault.
5. Define a trusted UserAccess mapping of Entra principal UPN → allowed EditionKey/StreamKey. RLS must filter facts through the matching trusted access mapping; bind `USERPRINCIPALNAME()` to assigned editions/streams. Test multiple-role unions, unknown users and historical access. No actual RLS role is embedded in these files. For the pilot, separate datasets per approved audience is safer than an unvalidated dynamic role.
6. RLS applies to report consumers in Viewer roles, not workspace Admin/Member/Contributor. Restrict workspace membership, Build permission, Analyze in Excel, export settings, sharing/resharing, subscriptions and downloads. Report-page hiding is not security. Verify Power BI sharing entitlement for every consumer and the current capacity/refresh limits. Never Publish to web.
7. Community analysis, if approved, uses self-reported values, explicit missing/unspecified categories, no forced grouping and protected aggregate output with a policy-approved small-cell threshold. Removing names does not make geography/community data anonymous; this sample is pseudonymous synthetic data. Community fields are deliberately omitted from this sample export.
8. Publish only after totals reconcile to source, RLS tests pass, freshness alerts work and the project owner accepts the viewer experience. Export genuine PBIP/PBIX from Desktop after successful model validation; do not treat these source recipes as a publishable report package.
''',
'power-bi/LoadCsv.pq':'''// Create text parameter DataFolder first; define this query as function LoadCsv.
(FileName as text) as table =>
let
    Source = Csv.Document(File.Contents(DataFolder & "/" & FileName),
        [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true])
in
    Headers
''',
'power-bi/measures.dax':'''// Add each measure separately in Power BI Desktop. Assign numeric types first.
Participants = DISTINCTCOUNT(FactParticipation[ParticipantKey])
Participations = COUNTROWS(FactParticipation)
Approved = CALCULATE([Participations], FactParticipation[ReviewStatus] = "Approved")
Registered = CALCULATE([Participations], FactParticipation[Registered] = 1)
Registration Completion = DIVIDE([Registered], [Approved])
Arrivals Confirmed = CALCULATE([Participations], FactParticipation[Arrived] = 1)
Departures Confirmed = CALCULATE([Participations], FactParticipation[Departed] = 1)
First-time Participations = CALCULATE([Participations], FactParticipation[IsFirstYear] = 1)
Repeat Participations = CALCULATE([Participations], FactParticipation[IsFirstYear] = 0)
Prior Year Participations =
VAR SelectedYear = SELECTEDVALUE(DimEdition[Year])
RETURN IF(NOT ISBLANK(SelectedYear), CALCULATE([Participations], REMOVEFILTERS(DimEdition), DimEdition[Year] = SelectedYear - 1))
YoY Growth = DIVIDE([Participations] - [Prior Year Participations], [Prior Year Participations])
// Denominator is approved nominations, not all drafts. Blank denominators stay blank.
// Repeat means seen in an earlier recorded edition; incomplete history can misclassify.
// Operational occupancy, meal, transport, attendance and payment measures require facts
// that are not exported by this initial model. Do not publish placeholder totals.
''',
'power-apps/BADGES.md':'''# Badge/QR status and licensing-compatible fallback

QR generation, PDF automation, revocation/reprint workflow and printable native badge layout are **not implemented**. A badge must contain only a random opaque token and approved display details, never contact, banking, document numbers or internal approval remarks. A scan must still authenticate the operator before it retrieves a record. Tokens must be revocable; they are not participant login credentials.

For a standard-connector pilot, use a simple organizer-printed badge with name, event edition, stream and human-readable opaque reference, after registration approval. Use an approved local Office template and print through an authorized workstation; do not send personal data to a public QR website. QR can be added only after evaluating a vetted locally bundled encoder/PCF control or an approved Microsoft-hosted QR service and its licensing/security implications. Power Apps barcode reader support does not imply QR generation support.

Word Online template actions and automated PDF conversions have connector/action-specific licensing and limitations; confirm in the tenant before selecting them. Browser/manual printing may avoid a premium PDF connector but does not deliver an automated issuance/reprint audit. That audit and approved print layout remain a Phase 2 gate.
''',
'user-guides/STAFF.md':'''# Staff pilot guide

This guide describes the local synthetic workbench. Microsoft screens must be built and tested before using the equivalent process with real staff.

1. Open the local URL printed by the developer command. Keep the synthetic-data warning visible. Select the current event edition.
2. Stream owner: choose New nomination, enter artificial details and Save draft. Open Participants and Submit the draft. You can only see your assigned test stream.
3. Reviewer: change the local test persona to Reviewer, search for the name, then Approve or Reject the submitted record. Production staff must use their own Entra account and cannot switch identities this way.
4. Registration: search by name prefix, exact phone or participation ID. Click Register for an approved nomination. Accommodation is independent; an approved participant without a room can register.
5. Accommodation: Confirm arrival, open Journey, choose an available bed, then Check in to bed. A second simultaneous allocation cannot take the occupied bed. Check out before confirming departure.
6. Transport, Kits or Food: open Journey, choose a service resource and record the action. The workbench rejects a full trip, exhausted stock or duplicate meal/kit issue. Actual eligibility policies and operational workflows are not complete.
7. Import: use the Excel template, export the Participants sheet as UTF-8 CSV, choose the file, Preview validation, correct errors, then Import valid rows. Download the row report. Each valid row becomes a draft. Existing duplicates need reviewer confirmation, not a second master.
8. If a save fails, refresh and search before re-entering. If “record changed” appears, refresh the participant and retry. Do not fix operational errors by deleting records.

During a future production outage, contact the authorized helpdesk and use the approved controlled fallback process. Never copy bank details or identity documents into a general spreadsheet or ordinary helpdesk ticket. Participant requests should be handled by an authenticated organizer showing only approved itinerary details. No participant portal is available yet.
''',
'tests/TENANT-UAT.md':'''# Mandatory tenant acceptance tests — NOT RUN

Use distinct real test accounts with synthetic records. Record actual result, tester, timestamp and evidence. Local tests do not satisfy this checklist.

- License administrator confirms exact app/flow/report entitlements and permitted hosting. No premium dependency hidden in a flow.
- Owner A creates/searches/imports only stream A. Owner B attempts direct list URL, REST query, SharePoint search and Excel connection to A: denied. Also test edits/deletes and guessed GUIDs.
- A volunteer/registration/analytics account attempts direct restricted identity, finance, health and review queue access: denied. Check attachments, versions, sharing links and search results. Broad site/member grants must not restore access.
- App sharing alone gives no new data access. A revoked role loses list/API access and flow authorization after membership/session propagation is verified. Multi-role users get only approved scopes.
- Snapshot edits after submission cannot alter what the reviewer approves. Rejection/correction/resubmission creates a new version. Forged stream/edition/role/email input is rejected. Reviewer identity comes from trusted editor/author metadata.
- Duplicate submissions, trigger redelivery and flow retries create one canonical participation, one ordinary kit issue and one audit transition. A conflicting retry payload fails.
- Kill the dispatcher after each reservation/write stage; resume without lost capacity or duplicate service. Concurrent requests for the last bed/seat/kit yield one winner. Verify room compatibility, accessibility, date overlaps and departures; these are not all implemented locally.
- With >5,000 records in one test list and multiple years, search a record beyond row 5,000, use exact ID/phone and prefix modes, compare full report totals and inspect delegation warnings/Monitor output. Repeat under expected peak operator concurrency.
- Check bank maker/checker/payer separation even when one user has multiple roles. Unauthorized direct status edits fail. External payment is recorded without claiming the app transfers funds.
- QR contains no personal fields; a token alone cannot authenticate. Revoked badge fails, reprint/replacement is audited. This feature is not implemented yet.
- Test accessibility at 360px width and keyboard-only operation, screen reader labels/error announcements, contrast, offline/slow network and duplicate taps. Browser rendering remains unverified in this environment.
- Validate Power BI RLS with Viewer accounts, not admins; ensure no vault columns in dataset; disable unapproved exports/Build/public links. Finance report is a separate boundary. Test small-cell suppression and refresh failure warnings.
- Restore a protected backup into a restricted site; reconcile receipt/audit/stock balances. Test approved retention deletion and legal holds.
- Participants cannot access other records or internal notes. Organizer-assisted view shares no account credentials. Power Pages/guest access requires separate auth/license/authorization tests before release.

Project owner signs off acceptance criteria 1–18 only when all applicable tests pass and all missing production modules are completed.
'''
}
for name,text in files.items():
 p=R/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
print('Wrote',len(files),'documentation and implementation-source files')
