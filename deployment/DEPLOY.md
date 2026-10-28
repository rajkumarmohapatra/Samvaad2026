# Deploy and open a Microsoft pilot

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
