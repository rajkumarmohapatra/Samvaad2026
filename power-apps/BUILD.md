# Canvas build status: manual creation required

No `.msapp`, `.pa.yaml` app, or solution ZIP has been fabricated. `Core.fx` contains independent property formulas, not one executable script. The native canvas app remains incomplete until created and tested in Studio.

1. Provision the pilot lists. Open https://make.powerapps.com in the chosen environment. Confirm standard SharePoint connector usage is licensed under your actual Microsoft 365 plan and DLP policy.
2. Create a responsive blank canvas app with modern controls and horizontal/vertical auto-layout containers. Set minimum mobile width to 360. Use theme colors #194F40, #F3F5F0 and #E7B56C. Keep labels visible and target sizes at least 44 px.
3. Create screens `CommandCenter`, `Participants`, `Nomination`, `ParticipantJourney`, `Reviewer`. Add the SharePoint data sources using the signed-in user's connection. Never share the automation account's connection with app users.
4. For a pilot, build **one stream-owner app per stream partition**. Bind its data source alias `Nominations` to `SB_Nominations_<CODE>`, and `StreamProjection` to `SB_Projection_<CODE>`. This is a maintenance compromise; a multi-partition scalable app needs tenant engineering. Do not construct arbitrary list names in a client and claim row security.
5. Add a search text control `txtSearch`, gallery `galParticipants`, edit form `frmNomination`, and the controls referenced by `Core.fx`. Attach the formulas property by property. Replace the two explicit configuration values with actual GUIDs. Add required field cards and configured hidden cards. Use choice controls for statuses/categories only when SharePoint field types match; this core schema uses text.
6. Add validation: `IsMatch(Trim(txtPhone.Text), "[0-9]{10,15}")`; require explicit participant-provided community information only when supplied voluntarily. Never infer it. Duplicate candidates require reviewer resolution, not automatic master merges. The tenant duplicate/import resolver is not yet built.
7. Reviewer app uses the separate `SB_ReviewQueue`; require a decision comment on rejection. Status edits are restricted to reviewer principals. Registration approval and identity status require separate operational modules not yet provisioned.
8. Error labels must announce form errors; use accessible labels on all controls, tab order, text status indicators, empty/loading states. Add a confirmation only for destructive operations. Do not promise autosave; this release uses explicit Save.
9. Configure the snapshot and promotion workflows from `power-automate/BUILD.md`. Do not display an editable nomination flag as approval status. Native SharePoint snapshots and immutable service receipts are authoritative.
10. Dashboard: use a protected aggregate list populated server-side by paginated scheduled flows, or Power BI. Do not use `CountRows(Filter(SharePointList,...))` as an accurate full-list count. The aggregate-list flow is not implemented in this package.
11. Save, run App Checker, verify delegation indicators, test with 6,000 rows and negative REST permissions, publish, then share with the matching Entra users/group. Sharing an app does not grant or restrict SharePoint access.

Current Microsoft Learn references (URLs verified 2026-10-27):
- [Canvas source files](https://learn.microsoft.com/en-us/power-apps/maker/canvas-apps/power-apps-yaml): do not rely on old `pac canvas pack/unpack` workflows for new native artifacts. Prefer Studio and supported solution export/import after tenant creation.
- [SharePoint connector](https://learn.microsoft.com/en-us/power-apps/maker/canvas-apps/connections/connection-sharepoint-online)
- [Delegation](https://learn.microsoft.com/en-us/power-apps/maker/canvas-apps/delegation-overview)

The multi-role command center, complete journey UI, localization files and native bulk import are release blockers. The local workbench demonstrates and tests a subset; it is not evidence that these native screens exist.
