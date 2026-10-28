// MANUAL STUDIO FORMULAS, not an importable canvas app or .msapp package.
// Bind aliases Nominations, StreamProjection and ReviewQueue to the provisioned
// lists for the current app/stream. SharePoint permissions enforce access.
// App.OnStart: no secrets or client-side role checks used as authorization.
Set(varEditionKey, "REPLACE_WITH_CONFIGURED_EDITION_GUID");
Set(varStreamKey, "REPLACE_WITH_THIS_PARTITION_STREAM_GUID");
Set(varSaving, false);
Set(varLocale, "en");

// galParticipants.Items — prefix search with delegable equality/StartsWith.
// Use a dedicated stream partition. Do NOT collect all records into a collection.
// Index EditionId and FullName; verify delegation with >5,000 seeded items.
SortByColumns(
    Filter(Nominations,
        EditionId = varEditionKey &&
        StartsWith(FullName, txtSearch.Text)
    ),
    "FullName", SortOrder.Ascending
)

// Exact ID search: separate control to avoid nondelegable Lower/concatenation.
LookUp(Nominations, RecordKey = Trim(txtExactId.Text))

// Exact phone search on indexed Phone. No phone normalization inside Filter.
Filter(Nominations, EditionId = varEditionKey && Phone = Trim(txtPhoneSearch.Text))

// btnSave.OnSelect — attached form has validation cards for required columns.
// SubmitForm supplies visible data cards and hidden configured IDs/timestamps.
// Clear request key only after success; retain it across uncertain network retries.
If(
    !varSaving && frmNomination.Valid,
    Set(varSaving, true);
    If(frmNomination.Mode = FormMode.New && IsBlank(varDraftKey), Set(varDraftKey, Text(GUID())));
    SubmitForm(frmNomination),
    Notify("Complete the highlighted required fields.", NotificationType.Warning)
)

// Hidden DataCard.Update values, configure individually in Studio:
// RecordKey: If(frmNomination.Mode = FormMode.New, varDraftKey, ThisItem.RecordKey)
// ClientRequestKey: If(frmNomination.Mode = FormMode.New, varDraftKey, ThisItem.ClientRequestKey)
// EditionId: varEditionKey
// StreamId: varStreamKey
// CreatedAt: If(frmNomination.Mode = FormMode.New, Now(), ThisItem.CreatedAt)
// UpdatedAt: Now()
// SubmitRequested: false
// FullName: Trim(txtFullName.Text)
// Phone: Trim(txtPhone.Text) — separate IsMatch validation before save.

// frmNomination.OnSuccess
Set(varSaving, false);
Set(varDraftKey, Blank());
Notify("Draft saved.", NotificationType.Success);
ResetForm(frmNomination);
Refresh(Nominations)

// frmNomination.OnFailure
Set(varSaving, false);
Notify("Save failed. Refresh and search for the draft before retrying. " & frmNomination.Error, NotificationType.Error)

// btnSubmit.OnSelect — requests a snapshot. This flag does not grant approval.
// Backend flow must bind EditionId/StreamId to its fixed partition, not trust fields.
IfError(
    Patch(Nominations, galParticipants.Selected,
        { SubmitRequested: true, UpdatedAt: Now() }),
    Notify("Submission could not be requested. Refresh and try again.", NotificationType.Error),
    Notify("Review requested. Approval remains pending until the snapshot workflow completes.", NotificationType.Success)
)

// lblStatus.Text — approvals come from owner-read-only projection, never nomination fields.
Coalesce(LookUp(StreamProjection,
    NominationRecordKey = galParticipants.Selected.RecordKey,
    ReviewStatus), "Review pending")

// Reviewer form updates ReviewQueue only. Separate reviewer app and backend list
// permission required; no service-account flow exposed via Run() from the canvas app.
// Notifications, approval processing and dashboard rollups require configured flows.
