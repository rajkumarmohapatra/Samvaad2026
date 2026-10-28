# Rules and release gates

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
