# Workbook field mapping and dashboard reference

Sources supplied by the project owner:

- `Samvaad 2026 Tribe Master + other data 26-10-26.xlsx`
- `Samvaad Dashboard R4 PDF.pdf`

The workbook was inspected for its schema. Its personal records and the raw attachments were not copied to the public GitHub repository or imported into the hosted participant database by this change. Dashboard values query authorised portal records. The PDF's fixed counts are a visual reference, not live totals. Its pages are labelled Samvaad 2025 even though its refresh timestamp is in October 2026; the app always identifies the selected event edition.

## Master Participants columns

| Source field | Native field or behavior |
|---|---|
| Error | Computed form/import/data-quality validation; not an editable participant identity field |
| ID | Participation.source_identifier; unique within an edition when supplied |
| Guest Name | Participant.name and annual Participation.name_snapshot |
| Gender | Optional self-reported Participant.gender |
| Category (Tribal/Non-Tribal) | Optional Participant.tribal_status; explicit Non-Tribal input normalises to Not Tribal |
| Tribe Type | Optional self-reported Participant.tribe_name; no inference |
| Country | Participant.country |
| State or UT1 | Participant.state_or_ut, preserving the supplied source classification |
| State | Participant.state and annual state snapshot |
| District | Participant.district |
| Area | Participant.village |
| PWD | Optional self-reported Participant.disability_status; clinical/emergency instructions remain in restricted Assistance |
| Participants Type | Participation.category, using administrator-configurable ParticipantCategory values |
| Samvaad Element Type | Primary stream/element assignment and annual stream label; only an enabled, classified unit can be selected |
| Valid ID Proof Type | Restricted IdentityRecord.document_type |
| ID Proof Number | Optional encrypted IdentityRecord.number_cipher, through the authorised identity screen only; never in general imports, charts, badges or notifications |
| Contact No. | Participant.phone; text, 10–15 digits, no numeric rounding |
| Email ID | Participant.email; validated email format |
| Accommodation Location | Relational Property/Room/Bed/Stay assignment; not an uncontrolled text overwrite of inventory |
| Unique QR No | Optional administrator-only legacy_qr_reference; new badge tokens are random and revocable |
| Samvaad Element Representative | Participation.element_representative; descriptive ownership label, not an access-control identity |
| Registration Status | Independent authorised registration workflow; not set by an untrusted import column |
| Registration SPOC | Participation.registration_spoc |
| KIT Provided | Audited KitIssue ledger, stock/eligibility/duplicate checks; not an editable Yes/No bypass |
| ID Status | Authorised identity verification status and badge issuance history |
| Remarks | Bounded operational remarks; no health, bank or identity numbers |
| Photoupload | Approved private photo_reference only; binary uploads/public sharing are not enabled by this release |
| Mode | Participation.registration_mode |
| Date and Time (Auto) | Portal created_at/updated_at; administrator-only source_created_at preserves an explicit source date |
| Item Type | Administrator-only source_item_type |
| Path | Administrator-only source_path, not a public sharing link |
| Check with NP | Review/duplicate-resolution validation; support records use the explicit attendee_group field |
| Tribe cat | Explicit tribal status/master reference; not inferred from source helper formulas |
| Adhar Len | Identity format validation; not a separately collected personal field |
| Name C | Duplicate-review check; no automatic identity merge |
| Aadhar count | Restricted identity verification concern; no raw identifier is included in public/general analytics |
| QR count | Unique opaque token constraint, revocation and duplicate checks |

`Master Non-Participants` and `Master Non-Participants (2)` are overlapping source sheets, not additive populations. Their fields share the schema above. The app provides an explicit Participant/Support grouping; it does not infer that group from tribal status. Extra source/helper columns such as Column1, Column2, C1-Adh, Issues and Tribe_Master2 are not accepted as authoritative workflow changes.

## Tribal Master

TribeReference supports unique code, national code, sub-code, tribe name, sub-tribe, state and active status. An optional participant linkage is explicitly selected; the participant's own wording is retained. Reference entries can be managed privately in Administration. The uploaded master was not silently imported or linked to people.

Flags such as Already reached, Joined this year, Calculation and Total Tribes are reporting outputs, not independent editable person attributes. Earlier-year and current-year comparisons require complete, reconciled history. Unknown history is not reported as zero reach.

## Dashboard coverage

- PDF overview: attendee records, registration, states and self-reported tribes; breakdowns by element, participant type, state, gender, tribal status and PWD.
- PDF operations: identity proof TYPE only; currently checked-in accommodation by property; kit distribution; record-creation trend.
- PDF detail: element/type cross-tab and registration SPOC/element cross-tab with complete server-side aggregates.
- Filters: state, district, tribe and tribal status where permitted, participant type, element, registration state and source/portal creation dates.
- State coverage is shown as an accessible bar chart rather than copying the PDF's licensed map tiles. Other high-cardinality charts use an Other groups bucket so displayed counts reconcile; complete matrices remain available.
- Demographic charts and filters require the separate `demographics.view` permission (superadministrators have access). Other users receive only their permitted views and records.
- Dates are displayed in IST. The creation trend is labelled as record creation; it is not falsely presented as actual arrival.

The portal template is the supported import schema. It accepts safe optional profile/ownership columns. Files with full identity numbers, photos or calculated helper columns are rejected with a clear error rather than silently retaining them in staged sessions. Restricted identity data uses the dedicated encrypted workflow.

## Notifications

The left-menu Notifications page stores operation events, page visits, sign-ins/sign-outs, validation alerts and denied requests. Records include the actual authenticated user, page name/route, severity, action and an automatic timestamp. Free-text form values, search queries, bank/identity numbers and private notes are not stored in notifications. Historical audit actions are backfilled with their original timestamps; historical page visits that were never recorded cannot be reconstructed.

Users see their own activity. Superadministrators see activity in the selected edition plus system events. An administrator can explicitly grant `notifications.view` for edition-wide oversight. Search/filter by user/page/action/message, date range, severity and read state; marking read respects the same backend scope.

## Dependencies and validation

The existing locked Django, openpyxl and cryptography dependencies cover this implementation. Charts are local SVG/CSS with no external CDN, mapping credential or additional JavaScript package. The deployment build collects the static assets. Additive schema migrations preserve existing participant records. Test coverage includes source IDs, optional field validation, imports, identity formats, chart/filter reconciliation, notification privacy/scoping, and invalid-date alerts.

Full browser accessibility review, peak-load tests, formal retention scheduling and automated external email/SMS delivery remain separate rollout work. This notification release stores alerts in the portal; it does not claim external message delivery.
