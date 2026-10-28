# Mandatory tenant acceptance tests — NOT RUN

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
