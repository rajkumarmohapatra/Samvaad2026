# Feasibility and architecture decision — 2026-10-28

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
