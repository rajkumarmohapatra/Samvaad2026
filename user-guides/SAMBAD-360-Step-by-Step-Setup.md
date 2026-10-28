# SAMBAD 360
## Microsoft 365 setup guide and copy-and-paste workbook

Prepared for the project owner | 28 October 2026 | Version 1.0

**Purpose:** Build a one-stream, synthetic-data pilot using SharePoint, Power Apps, Power Automate and Power BI. This is a practical setup workbook, not a claim that the complete platform has been deployed.

**Current access limitation:** The connected Microsoft account resolved to personal OneDrive. An organisational Microsoft 365 work/school account, appropriate permissions and confirmed licensing are required for the tenant steps below. Do not put organisational participant records in a personal OneDrive account.

**What you can complete with this guide:** a protected SharePoint draft list; a three-screen canvas application that creates, edits and searches synthetic nominations; an initial reporting model using supplied synthetic CSVs. Approval integration is a developer-led milestone described separately. Accommodation, travel, finance, kits, food, participant self-service and full native imports are not completed by these steps.

**Production gate:** Do not load real participant, banking, identity or health data until backend permissions, workflow validation, retention, licensing and acceptance testing have been signed off. The local 36-test result is not evidence of tenant security or production readiness.

# 1. Read this first

The four Microsoft components have different jobs:

| Component | Job | Where to open it |
|---|---|---|
| SharePoint | Store data and enforce list/site permissions | Your organisation's SharePoint site |
| Power Apps | Provide staff screens and forms | https://make.powerapps.com |
| Power Automate | Process protected submissions, reviews and retries | https://make.powerautomate.com |
| Power BI | Build and share reporting | Power BI Desktop; https://app.powerbi.com |

Build in that order. Power BI can also be tried immediately using the supplied synthetic CSVs. Menu wording may vary by tenant and release. Do not buy a trial or enable premium connectors just to get past an error; ask your administrator to confirm the approved licensing route.

## 1.1 Who does what

| Person | Responsibility |
|---|---|
| Project owner | Approves stream classification, data purposes, access and acceptance |
| Microsoft 365/SharePoint administrator | Confirms tenant/licences, prepares site and permissions |
| Power Apps maker | Builds, validates and publishes screens |
| Power Automate maker | Builds server-validated workflows and recovery |
| Power BI author | Builds model, validates totals, configures access and refresh |
| Test stream owner and reviewer | Perform tests using separate accounts |

One person can hold more than one delivery responsibility, but testing must include distinct user accounts. Finance maker/checker/payer separation remains a later mandatory control.

## 1.2 Files to keep together

Extract the downloaded foundation ZIP into a folder such as `C:\Sambad360\sambad-360`. Keep the internal subfolders unchanged. The copy pack accompanying this guide contains one `.txt` or `.json` file for each major snippet so you can copy code without Word changing its punctuation.

# 2. Fill in your configuration register

Replace text in angle brackets before copying a configuration formula. Never put passwords or tokens in this register.

| Setting | Your value |
|---|---|
| Work/school account | ______________________________ |
| Microsoft 365 tenant | ______________________________ |
| SharePoint pilot site URL | ______________________________ |
| Power Apps environment | ______________________________ |
| Event RecordKey | ______________________________ |
| Edition RecordKey | ______________________________ |
| Pilot stream RecordKey | ______________________________ |
| Pilot stream code | PILOT |
| SharePoint owner group | ______________________________ |
| App owner and backup owner | ______________________________ |
| Workflow owner and backup owner | ______________________________ |
| Power BI workspace | ______________________________ |

A RecordKey is an application-generated UUID/GUID stored as text. SharePoint also creates a separate numeric `ID`. Keep both concepts separate: forms use RecordKey for application references; connector Get item actions normally use SharePoint's numeric ID.

Generate a new GUID in PowerShell with the following command, or use an organisation-approved tool. No tenant authentication is needed merely to generate a GUID.

```powershell
[guid]::NewGuid().ToString()
```

Create three GUIDs and record them as Event, Edition and Stream keys. Do not reuse one GUID for all three.

# 3. Confirm licences and create a private SharePoint site

1. Ask the administrator to verify your work/school account, SharePoint site creation rights, Power Apps maker rights and standard SharePoint connector entitlement.
2. Confirm automation ownership/usage rules and Power BI sharing entitlement for the intended viewers. Power BI Desktop authoring and online report sharing are different licensing questions.
3. Create an owners-only pilot SharePoint site named `SAMBAD 360 Pilot`. A private team site may still have broad Members-group grants; private is not the same as correctly permissioned.
4. Record the site URL, for example `https://<tenant>.sharepoint.com/sites/Sambad360Pilot`.
5. Open Settings > Site permissions > Advanced permissions settings. Have the administrator inspect the owners, members, visitors, direct grants and sharing policy.
6. Keep at least one authorised administrator with Full Control. Do not remove your only administrator.
7. Disable or prohibit anonymous/public sharing under the approved tenant policy. Do not create anyone-with-link links.

**Checkpoint:** A normal test user who has not been assigned a pilot group must not be able to browse the participant lists. A site title or a hidden navigation link is not a permission control.

# 4. Create groups and a safe writer permission level

Use Site permissions > Advanced permissions settings. Create these SharePoint groups without giving them blanket site-wide participant access:

```text
SB Config Readers
SB Stream PILOT
SB Reviewers
SB Registration Readers
SB Automation
```

The supplied provisioning script creates these groups. If you use that script, do not duplicate them manually.

Create a custom list writer permission level named `SB Draft Editor`: copy the built-in Read level, then add Add Items, Edit Items and View Versions. Exclude Delete Items, Delete Versions, Manage Lists and Manage Permissions. A SharePoint administrator should verify the effective permissions.

Create an `SB Append Only` level from Read plus Add Items for the audit writer. Read access still allows retrieval through APIs and may permit exports; an Export button hidden by Power Apps does not prevent data extraction.

| Group | Pilot membership | Data access |
|---|---|---|
| Owners | Small named admin group | Privileged configuration |
| SB Config Readers | Approved staff who need configuration | Read configuration lists |
| SB Stream PILOT | Pilot stream owners | Edit pilot nominations; read pilot projection |
| SB Reviewers | Trusted reviewers | Read nominations; edit protected review queue |
| SB Registration Readers | Authorised registration readers | Read minimal operational projection |
| SB Automation | Dedicated workflow account only | Required protected writes; no normal staff membership |

Do not make ordinary staff site Members or Owners as a shortcut. Stream owners must not inherit reviewer or automation access.

# 5. Create the SharePoint lists

Choose ONE approach: A, administrator provisioning; or B, manual creation for the draft-entry milestone. Do not run both blindly against the same partially configured lists.

## 5A. Administrator provisioning (recommended)

The administrator installs a currently supported PowerShell/PnP.PowerShell version and obtains the organisation-approved Entra app client ID for delegated interactive sign-in. PnP is a community-supported administration tool and its use must fit organisational policy. The script has not been executed against your tenant.

Copy this JSON into `deployment\streams.pilot.json`:

```json
[
  {
    "code": "PILOT",
    "name": "Pilot Stream"
  }
]
```

Open PowerShell in the extracted repository root. Review the script first. Preview the operation:

```powershell
.\sharepoint\Provision-Core.ps1 `
  -SiteUrl "https://<tenant>.sharepoint.com/sites/Sambad360Pilot" `
  -ClientId "<approved-entra-application-client-id>" `
  -StreamConfiguration ".\deployment\streams.pilot.json" `
  -PrivateSiteVerified `
  -WhatIf
```

After administrator review, run the same command without `-WhatIf`. Sign in through the normal Microsoft sign-in window. Do not paste credentials into the script. The strict script requires only the owner group to have site-wide grants; see `deployment/DEPLOY.md` if it refuses a Members/Visitors grant.

Expected lists: `SB_Events`, `SB_EventEditions`, `SB_OrganizationalUnits`, `SB_EditionUnits`, `SB_Nominations_PILOT`, `SB_ReviewQueue`, `SB_Projection_PILOT`, `SB_ParticipationSnapshots`, `SB_AuditEvents`, `SB_WorkflowReceipts`. Add FullName and Phone indexes to the nominations list after provisioning; verify the other configured indexes. Existing lists are skipped, not migrated or certified. A partial failure needs manual inspection before retrying.

## 5B. Manual creation for the draft-entry app

In SharePoint select New > List > Blank list. Name it exactly:

```text
SB_Nominations_PILOT
```

Create the columns below using exactly the internal names shown. Create the name without spaces initially; display names can be made friendlier later. Do not create Phone as a Number field: leading zeros and formatting matter.

| Column | SharePoint type | Required | Additional setting |
|---|---|---|---|
| RecordKey | Single line of text | Yes | Enforce unique values |
| CreatedAt | Date and time, include time | Yes | Application timestamp |
| UpdatedAt | Date and time, include time | Yes | Application timestamp |
| EditionId | Single line of text | Yes | Indexed |
| StreamId | Single line of text | Yes | Indexed |
| FullName | Single line of text | Yes | Indexed |
| Phone | Single line of text | Yes | Indexed |
| State | Single line of text | Yes | Plain text |
| District | Single line of text | No | Plain text |
| Community | Multiple lines of text | No | Plain text; no rich text |
| Category | Single line of text | Yes | Dropdown values supplied by app |
| ClientRequestKey | Single line of text | Yes | Enforce unique values |
| SubmitRequested | Yes/No | Yes | Default No |

Set the default Title column to not required. Enable list version history and disable attachments for this list. In List settings > Permissions for this list, stop inheriting permissions, retain administrator access, remove broad copied grants and assign the exact groups described in Section 4. Grant the stream group `SB Draft Editor`, reviewers Read, and the dedicated automation group only the needed writer level.

The manual draft app does not require the workflow lists yet. Before approval integration, provision the remaining core lists using the exact definitions in `sharepoint/core-lists.json`. Do not improvise field names or pretend the manual list alone provides a protected approval workflow.

## 5.1 Enter configuration records

If you provisioned the full core, create these four configuration records. Fill all required fields from `data-model/dictionary.md`; the following table explains the references.

| List | Record | Important references |
|---|---|---|
| SB_Events | Sambad | RecordKey = Event key; EventCode = SAMBAD; Active = Yes |
| SB_EventEditions | Your pilot edition | RecordKey = Edition key; EventId = Event key; Year/dates = owner-approved values; Status = Open |
| SB_OrganizationalUnits | Pilot Stream | RecordKey = Stream key; UnitCode = PILOT; Kind = Stream; Active = Yes |
| SB_EditionUnits | Stream enabled for edition | EditionId = Edition key; UnitId = Stream key; OwnerGroupId = actual SharePoint group ID |

Every record also needs its own RecordKey, CreatedAt and UpdatedAt. The EditionUnits record has its own fourth GUID. Event dates in examples are not confirmed Sambad dates. Use the project owner's approved dates.

For the manual draft-only milestone, recording the three generated keys in the register is enough to test form saving. The configuration-list records and server-side edition/stream validation must be completed before real operations.

# 6. Build the first Power Apps application

Open https://make.powerapps.com with the work/school account. Select the approved environment. Create a blank canvas app named `SAMBAD 360 - Pilot Stream`. Use responsive auto-layout containers where possible. Menu labels may differ; do not accept a premium trial prompt without the administrator's decision.

This workbook uses CLASSIC Text input and Drop down controls so `.Text` and `.Selected.Value` formulas are consistent. Modern controls can have different properties.

## 6.1 Add the SharePoint data source

Select Data > Add data > SharePoint. Connect using the authorised user's connection, enter the pilot SITE URL and select `SB_Nominations_PILOT`. Select the list itself, not an Excel workbook. Keep the data source name as shown. Never share the workflow account's connection with staff.

Create three blank screens named exactly:

```text
scrHome
scrParticipants
scrNomination
```

Set `App.StartScreen` to:

```powerfx
scrHome
```

Set `App.OnStart` to the following AFTER replacing the two keys with the values in your register:

```powerfx
Set(varEditionKey, "<edition-recordkey>");
Set(varStreamKey, "<stream-recordkey>");
Set(varSaving, false);
Set(varDraftKey, Blank());
Set(varSelectedNomination, Blank())
```

Run App.OnStart in Studio after changing it, or reopen Preview. These values are configuration, not authorisation. Server-side flows must validate scope later.

## 6.2 Build the home screen

Add a heading `SAMBAD 360`, a subtitle `Pilot - synthetic data only`, and a button named `btnOpenParticipants`. Set its Text to `Participants`. Set its OnSelect to:

```powerfx
Refresh(SB_Nominations_PILOT);
Navigate(scrParticipants, ScreenTransition.None)
```

Do not add a full-list participant total with `CountRows` over SharePoint. That is not an accurate scalable dashboard count. Use the Power BI report or a separately implemented server-produced aggregate.

## 6.3 Build participant search

On `scrParticipants` add a classic Text input named `txtSearch`, a vertical gallery named `galParticipants`, and a New nomination button named `btnNewNomination`. Set txtSearch.Default to an empty string and HintText to `Search by name prefix`.

Set galParticipants.Items to:

```powerfx
SortByColumns(
    Filter(
        SB_Nominations_PILOT,
        EditionId = varEditionKey &&
        StartsWith(FullName, txtSearch.Text)
    ),
    "FullName",
    SortOrder.Ascending
)
```

Inside the gallery, set the title label's Text to `ThisItem.FullName`, the subtitle to `ThisItem.Category`, and a smaller label to `ThisItem.RecordKey`. A gallery template button labelled Edit draft should have:

```powerfx
Set(varSelectedNomination, ThisItem);
Set(varDraftKey, ThisItem.RecordKey);
Reset(txtFullName);
Reset(txtPhone);
Reset(txtState);
Reset(txtDistrict);
Reset(txtCommunity);
Reset(ddCategory);
Navigate(scrNomination, ScreenTransition.None)
```

Create the controls in Section 6.4 before resolving their names in this formula. Set btnNewNomination.OnSelect to:

```powerfx
Set(varSelectedNomination, Blank());
Set(varDraftKey, Text(GUID()));
Reset(txtFullName);
Reset(txtPhone);
Reset(txtState);
Reset(txtDistrict);
Reset(txtCommunity);
Reset(ddCategory);
Navigate(scrNomination, ScreenTransition.None)
```

A filtered gallery is not a backend permission boundary. Another stream must have a separately permissioned list for this pilot approach. The final multi-stream app needs additional engineering.

## 6.4 Build the nomination screen

On scrNomination create the following classic controls and labels. Use multiline mode for Community. Set each control's Default as below; this lets a saved draft be edited.

| Control name | Control type | Default property |
|---|---|---|
| txtFullName | Text input | Coalesce(varSelectedNomination.FullName, "") |
| txtPhone | Text input | Coalesce(varSelectedNomination.Phone, "") |
| txtState | Text input | Coalesce(varSelectedNomination.State, "") |
| txtDistrict | Text input | Coalesce(varSelectedNomination.District, "") |
| txtCommunity | Multiline Text input | Coalesce(varSelectedNomination.Community, "") |
| ddCategory | Classic Drop down | Coalesce(varSelectedNomination.Category, "Delegate") |

Use these Items for ddCategory:

```powerfx
["Delegate", "Artist", "Artisan", "Volunteer", "Other"]
```

These are pilot choices, not a replacement for the final configurable category master. Label community as `Self-reported community (optional)` and do not infer or force a classification.

Add buttons `btnSaveDraft` and `btnCancel`. Set btnSaveDraft.DisplayMode to:

```powerfx
If(varSaving, DisplayMode.Disabled, DisplayMode.Edit)
```

Set btnSaveDraft.OnSelect to the following complete draft-save formula. It fills every required field in the specified nominations schema. It preserves keys/timestamps and the submission flag on edits. It does not implement approvals, duplicate identity resolution or backend scope validation.

```powerfx
If(
    IsBlank(Trim(txtFullName.Text)) ||
    IsBlank(Trim(txtState.Text)) ||
    !IsMatch(
        Trim(txtPhone.Text),
        "[0-9]{10,15}",
        MatchOptions.Complete
    ),
    Notify(
        "Enter a name, state and a phone with 10 to 15 digits.",
        NotificationType.Warning
    ),
    Set(varSaving, true);
    If(IsBlank(varDraftKey), Set(varDraftKey, Text(GUID())));
    IfError(
        Set(
            varSavedNomination,
            Patch(
                SB_Nominations_PILOT,
                If(
                    IsBlank(varSelectedNomination.ID),
                    Defaults(SB_Nominations_PILOT),
                    varSelectedNomination
                ),
                {
                    RecordKey: varDraftKey,
                    ClientRequestKey: If(
                        IsBlank(varSelectedNomination.ID),
                        varDraftKey,
                        varSelectedNomination.ClientRequestKey
                    ),
                    EditionId: varEditionKey,
                    StreamId: varStreamKey,
                    FullName: Trim(txtFullName.Text),
                    Phone: Trim(txtPhone.Text),
                    State: Trim(txtState.Text),
                    District: Trim(txtDistrict.Text),
                    Community: Trim(txtCommunity.Text),
                    Category: ddCategory.Selected.Value,
                    CreatedAt: If(
                        IsBlank(varSelectedNomination.ID),
                        Now(),
                        varSelectedNomination.CreatedAt
                    ),
                    UpdatedAt: Now(),
                    SubmitRequested: Coalesce(
                        varSelectedNomination.SubmitRequested,
                        false
                    )
                }
            )
        );
        Set(varSaving, false);
        Notify("Draft saved.", NotificationType.Success);
        Refresh(SB_Nominations_PILOT);
        Navigate(scrParticipants, ScreenTransition.None),
        Set(varSaving, false);
        Notify(
            "Save could not be confirmed. Refresh and search before retrying.",
            NotificationType.Error
        )
    )
)
```

Set btnCancel.OnSelect to:

```powerfx
Navigate(scrParticipants, ScreenTransition.None)
```

An uncertain network result may mean the first save succeeded. Refresh and find the RecordKey before retrying. A unique-key rejection prevents a second record with the same key; it is not the full user-friendly retry resolver. This initial screen also lacks optimistic-concurrency conflict handling for simultaneous draft edits. Both are production release gates.

## 6.5 Optional exact searches

For a separate gallery/search mode, use indexed Phone equality rather than transforming every phone inside Filter. With a classic input named txtPhoneSearch:

```powerfx
Filter(
    SB_Nominations_PILOT,
    EditionId = varEditionKey &&
    Phone = Trim(txtPhoneSearch.Text)
)
```

For a separate exact application-ID lookup with txtExactId:

```powerfx
LookUp(
    SB_Nominations_PILOT,
    RecordKey = Trim(txtExactId.Text)
)
```

Do not combine these examples into a complicated OR search without delegation testing. Do not use Lower, Distinct or a local collection of the first 2,000 rows as if it contains the full SharePoint dataset.

## 6.6 Preview, save and share the draft-only pilot

1. Run App Checker and fix missing-control/type errors. Check delegation warnings on search.
2. In Preview, enter `Synthetic Participant 001`, a clearly artificial 10-digit test value, `Synthetic State`, and Delegate. Do not contact any number entered for testing.
3. Save and check that exactly one row appeared in SharePoint with the configured edition/stream keys.
4. Edit the draft; confirm its RecordKey and CreatedAt stay the same.
5. Search by its name prefix. Test keyboard navigation, phone width, readable labels and error messages.
6. Save and publish the app version. Share only with the approved pilot users/group. They also need the intended SharePoint permissions.
7. Give staff the actual app Play link from Power Apps. A local workbench URL is not the Power Apps link.

**Milestone A:** You now have a synthetic draft-entry pilot. You do not yet have an approved participant registry, native bulk importer, participant portal or complete operating platform.

# 7. Add protected submissions and approvals - developer milestone

This section is a construction checklist for the maker and administrator. It is not an importable flow or an assertion that a simple flag/approval-email flow is production-safe. The exact snapshot, canonical master resolver, permission checks and recovery still require implementation and tenant testing.

## 7.1 Authoritative data boundaries

- Nominations: editable source drafts for one stream.
- ReviewQueue: protected snapshot of the exact source version being reviewed.
- Participation master/year records: canonical records created only after approved duplicate/identity resolution; not fully provisioned by the current core package.
- StreamProjection: minimal, owner-read-only status view, including the source NominationRecordKey and a separate canonical ParticipationId.
- WorkflowReceipts and AuditEvents: protected durable progress and traceability.

Do not display an editable nomination flag as an approval decision. Do not treat a nomination RecordKey as the canonical ParticipationId. Preserve the mapping explicitly.

## 7.2 Add a submission request button only when the receiver exists

In the owner app, a gallery template button may request review with this formula. Enable it only after the receiving flow is configured and tested.

```powerfx
IfError(
    Patch(
        SB_Nominations_PILOT,
        ThisItem,
        { SubmitRequested: true, UpdatedAt: Now() }
    ),
    Notify("Submission failed. Refresh and try again.", NotificationType.Error),
    Notify("Review requested; approval is pending.", NotificationType.Success)
)
```

This does not lock the source record and does not confer approval. A production submission-command approach must handle repeated submissions and concurrent edits safely.

## 7.3 Build the snapshot flow

1. Open https://make.powerautomate.com in the approved environment. Use the dedicated approved connection; protect flow ownership.
2. Create an automated cloud flow named `SAMBAD - PILOT - Snapshot Submission`.
3. Select SharePoint trigger `When an item is created or modified` and bind it to the fixed site and `SB_Nominations_PILOT`.
4. In trigger settings, enable concurrency control with degree 1. Add the trigger condition below.
5. Add SharePoint Get item, name it `Get_nomination`, and use the numeric ID from the trigger.
6. Validate the trusted actual editor/author identity, its server-side group/scope, configured edition and allowed fields. Fail closed if membership cannot be resolved. Do not trust an input email, role or edited StreamId.
7. Capture the returned source version and create a unique server-derived request key. Use a fixed partition/list identifier, numeric source ID and submitted version. Check/create a WorkflowReceipts row; a duplicate key means inspect/resume its recorded stage, not silently succeed.
8. Build the whitelisted snapshot object described below. Create/reuse the ReviewQueue row with NominationKey, SourceVersion, configured edition/stream, Snapshot and Status = Submitted. Supply its RecordKey, CreatedAt and UpdatedAt.
9. Update the receipt to SnapshotCreated with the target review row ID. Append a redacted audit event.
10. Clear SubmitRequested only through an ETag-conditional update against the fetched source version. On 412 re-read and resolve the conflict; never overwrite a newer request with IF-MATCH: *.
11. Add Try/Catch/failure scopes, bounded retry handling, protected dead-letter records and scheduled receipt reconciliation. Trigger concurrency 1 does not provide a multi-list transaction.
12. Test source changes, duplicate trigger delivery and a failure after every durable write. Do not enable operational use until recovery is demonstrated.

Trigger condition to copy:

```text
@equals(triggerBody()?['SubmitRequested'], true)
```

In a Compose action, build an OBJECT using these properties and dynamic values. Insert expression values in the designer expression editor; do not paste the table itself as JSON or copy a source record wholesale.

| Snapshot property | Expression/value |
|---|---|
| NominationRecordKey | body('Get_nomination')?['RecordKey'] |
| FullName | body('Get_nomination')?['FullName'] |
| Phone | body('Get_nomination')?['Phone'] |
| State | body('Get_nomination')?['State'] |
| District | body('Get_nomination')?['District'] |
| Community | body('Get_nomination')?['Community'] |
| Category | body('Get_nomination')?['Category'] |
| EditionId | Server-configured edition key, not trusted from caller |
| StreamId | Server-configured stream key, not trusted from caller |

Use the actual SharePoint version dynamic content returned by your connector; field names can vary. This must be verified in the tenant rather than guessed. Enable Secure Inputs/Outputs on actions that contain private data and restrict run-history access.

Useful expression blocks:

```text
utcNow()
```

```text
guid()
```

```text
workflow()?['run']?['name']
```

## 7.4 Review and promotion

Create a separate reviewer app or a protected List form connected to SB_ReviewQueue. Only trusted reviewers can access it. Display the submitted snapshot and source version. Capture Approved or Rejected; require a safe rejection reason. The authoritative reviewer identity comes from the actual SharePoint editor metadata, not a typed ReviewerId field.

A separate protected workflow must validate the reviewer, read the approved snapshot, resolve participant duplicates/cross-year reuse, write canonical annual participation and publish the minimal projections. Later edits to the original nomination must not change the reviewed content. Write NominationRecordKey into the projection so owner status lookup can find it.

After connecting SB_Projection_PILOT to the owner app, a gallery label can use:

```powerfx
Coalesce(
    LookUp(
        SB_Projection_PILOT,
        NominationRecordKey = ThisItem.RecordKey,
        ReviewStatus
    ),
    "No review result published"
)
```

No result may mean no submission or an unfinished workflow; it is not proof of rejection. A dedicated submission-status projection is needed for precise intermediate states.

Notification outboxes can reduce repeated sends, but an uncertain send result can still duplicate email. Make state changes idempotent independently of notifications. Full construction details are in `power-automate/BUILD.md` and `workflows.json`.

**Milestone B:** The maker demonstrates one version-bound submission, authorised review, canonical promotion, protected projection and safe recovery with separate accounts. This milestone is incomplete until built and tested in the tenant.

# 8. Build the first Power BI report

This section uses the supplied synthetic CSVs. It can be completed before workflow development, but it will not automatically read live app changes.

## 8.1 Import data in Power BI Desktop

1. Install/open Power BI Desktop on an approved Windows computer.
2. Select Get data > Text/CSV. From `power-bi\sample-data`, load the four CSVs named below. Use Transform Data to check types and headers.
3. The files are synthetic reporting samples, not a native Power Apps export and not production data.

| File/table | Meaning | Required types |
|---|---|---|
| FactParticipation | One participant in one edition | Keys/text; Arrived, Registered, Departed, IsFirstYear = Whole number |
| DimEdition | Event-year dimension | EditionKey = Text; Year = Whole number; Starts/Ends = Date |
| DimStream | Stream dimension | StreamKey/Name = Text |
| DimParticipant | Pseudonymous synthetic participant dimension | ParticipantKey/State/District = Text |

In Model view, create single-direction, one-to-many relationships:

```text
DimEdition[EditionKey]  1 -> *  FactParticipation[EditionKey]
DimStream[StreamKey]    1 -> *  FactParticipation[StreamKey]
DimParticipant[ParticipantKey]  1 -> *  FactParticipation[ParticipantKey]
```

Do not connect dimensions to each other or turn on bidirectional filtering to make a visual appear to work. Check uniqueness on the dimension side.

## 8.2 Paste DAX measures one at a time

Choose Modeling > New measure for EACH block. These are measures, not calculated columns or Power Query expressions.

```dax
Participations = COUNTROWS(FactParticipation)
```

```dax
Participants = DISTINCTCOUNT(FactParticipation[ParticipantKey])
```

```dax
Approved =
CALCULATE(
    [Participations],
    FactParticipation[ReviewStatus] = "Approved"
)
```

```dax
Registered =
CALCULATE(
    [Participations],
    FactParticipation[Registered] = 1
)
```

```dax
Registration Completion = DIVIDE([Registered], [Approved])
```

```dax
Arrivals Confirmed =
CALCULATE(
    [Participations],
    FactParticipation[Arrived] = 1
)
```

```dax
Repeat Participations =
CALCULATE(
    [Participations],
    FactParticipation[IsFirstYear] = 0
)
```

```dax
First-time Participations =
CALCULATE(
    [Participations],
    FactParticipation[IsFirstYear] = 1
)
```

```dax
Prior Year Participations =
VAR SelectedYear = SELECTEDVALUE(DimEdition[Year])
RETURN
IF(
    NOT ISBLANK(SelectedYear),
    CALCULATE(
        [Participations],
        REMOVEFILTERS(DimEdition),
        DimEdition[Year] = SelectedYear - 1
    )
)
```

```dax
YoY Growth =
DIVIDE(
    [Participations] - [Prior Year Participations],
    [Prior Year Participations]
)
```

Format Registration Completion and YoY Growth as percentages. A blank denominator should remain blank, not become a misleading zero. Repeat means recorded in an earlier edition; incomplete history may misclassify people. Prior Year Participations and YoY Growth expect one selected year; use the Year dimension as the visual axis for a trend.

## 8.3 Build three report pages

| Page | Visual | Fields/measure |
|---|---|---|
| Command center | Single-select slicer | DimEdition[Year] |
| Command center | Cards | Participations, Approved, Registered, Registration Completion, Arrivals Confirmed |
| Participation | Bar chart | DimStream[Name] + Participations |
| Participation | Bar chart | DimParticipant[State] + Participants |
| Participation | Matrix | State, District, Participants |
| Historical | Column chart | DimEdition[Year] + Participations |
| Historical | Cards | First-time Participations, Repeat Participations, YoY Growth |

Import `power-bi/theme.json` through View > Themes > Browse for themes if the installed Desktop version supports the supplied theme. Use readable labels and text status indicators. Do not add occupancy, meals, payments or transport cards showing zero: those source facts are not in this sample model.

## 8.4 Reconcile your report

With Year = 2026 selected in the unmodified supplied sample:

| Metric | Expected synthetic result |
|---|---|
| Participations | 3,000 |
| Participants | 3,000 |
| Approved | 1,800 |
| Registered | 450 |
| Registration Completion | 25% |
| Arrivals Confirmed | 600 |
| Repeat Participations | 600 |
| First-time Participations | 2,400 |

With no year filter, Participations = 3,600 and distinct Participants = 3,000. A mismatch usually means a missing/wrong relationship, numeric flags loaded as text, or an unexpected filter. These figures come from the sample dataset, not the generated visual concept image and not a real event.

## 8.5 Save and publish a restricted pilot

1. Save the Desktop report as `SAMBAD360-Pilot.pbix` on an approved device.
2. Confirm the intended workspace and viewer licensing before Publish. Do not acquire a trial or widen permissions as a workaround.
3. Publish only the reviewed synthetic report to the approved pilot workspace.
4. Give consumers Viewer access or distribute through an approved Power BI app audience. Workspace Admin/Member/Contributor roles are privileged and not protected by ordinary consumer RLS in the same way.
5. Restrict Build, exports and resharing according to policy. Never use Publish to web.
6. This guide's initial report has no configured dynamic RLS. Do not share an all-stream production dataset with stream owners until the security model is implemented and tested. Separate audience-specific models are a possible pilot compromise.

A local CSV file connection does not become a cloud refresh connection merely because the PBIX was published. Refresh needs a configured gateway for local sources or an approved cloud source. For the final report, prefer a protected SharePoint analytics projection and cloud credentials rather than a desktop folder dependency.

## 8.6 Connect to real operational data only after the projection exists

In Power BI Desktop, Get data > SharePoint Online List accepts the SITE URL. Connect only to approved analytics projection lists containing minimal reporting fields. The core SB_ParticipationSnapshots schema does not contain all fields in FactParticipation and cannot simply replace it without a mapping/transformation and additional source facts.

The production analytics projection, extraction, full operational facts, RLS, refresh monitoring and data-quality checks are still development tasks. Never source a general report from banking documents, full bank details, identity files or health cases. Display the last successful refresh time. SharePoint-backed import reports are not automatically real time.

# 9. Create a SharePoint landing page

After the app and report are published and independently permission-tested:

1. Open the pilot site's home page and select Edit.
2. Add a Power Apps web part and enter the published app identifier requested by the web part. Use the app's actual details/Play link.
3. In Power BI service, open the reviewed report and use File > Embed report > SharePoint Online where available. Copy the approved report link.
4. Add a Power BI web part to SharePoint and paste that link.
5. Add Quick Links to staff instructions and helpdesk contact information.
6. Publish the SharePoint page and test with a normal staff account.

Embedding does not grant Power Apps, SharePoint or Power BI permissions/licences. A visible web part can still display Access denied until the appropriate permissions are configured. Do not fix that by making data public.

# 10. Pilot acceptance checklist

Use separate test identities and record evidence. An administrator testing as themselves cannot prove that an ordinary user is restricted.

| Test | Pass condition | Result |
|---|---|---|
| Draft creation | One record; correct keys and required values | ______ |
| Draft edit | Same RecordKey and CreatedAt; updated values | ______ |
| Search | Correct name-prefix and exact-ID results | ______ |
| Invalid input | Clear error; no save | ______ |
| Cross-stream list/API access | Denied for unassigned user | ______ |
| Approval access | Stream owner cannot edit reviewer-only records | ______ |
| Version-bound review | Approved content matches reviewed snapshot | ______ |
| Retry recovery | No duplicate canonical participation or service issue | ______ |
| Reporting totals | Match Section 8.4 for supplied sample | ______ |
| Report sharing | Correct audience; no public link; RLS tested if used | ______ |
| Accessibility | Keyboard, phone layout, labels and errors usable | ______ |
| Licensing | Administrator has confirmed actual entitlements | ______ |

Scale-test SharePoint search with more than 5,000 synthetic items in a single test list, including records beyond the first 2,000, before declaring search complete. A delegation row-limit increase is not a fix. Test multiple simultaneous users and workflow fault recovery before enabling bed/vehicle/stock allocation.

# 11. Troubleshooting and safe recovery

| Symptom | Check / safe next action |
|---|---|
| Personal OneDrive appears | Connect the correct organisation work/school Microsoft account |
| Cannot create site/list | Ask administrator for intended permissions; do not switch to a public/personal store |
| Data source is missing | Confirm environment, site URL, list permissions and connector policy |
| Formula has unknown control | Rename the control exactly; check classic vs modern properties |
| Formula punctuation errors | Verify authoring locale; some locales use semicolons for arguments and double semicolons for action chaining |
| Patch says required field missing | Compare schema, Title required setting and every required metadata field |
| Unique-key save failure | Search for existing RecordKey; first uncertain save may already have succeeded |
| Only some records appear | Inspect delegation warnings, indexes, edition filter and permissions; do not trust a 2,000-row collection |
| Submitted but no approval result | Check protected flow run, receipt and review queue; flag alone is not approval |
| Power BI totals differ | Check filters, data types, dimension uniqueness and single-direction relationships |
| SharePoint Power BI web part says access denied | Confirm Power BI audience/licence separately from SharePoint page access |
| Report refresh fails | Local file paths need gateway/cloud-source redesign; validate credentials and refresh history |

SharePoint version history/recycle bin is not a complete backup plan. Arrange an approved backup/restore process and records schedule before production. Do not delete workflow receipts or allocations simply to make a failed process look successful.

# 12. What comes after this pilot

Complete the protected participant master/year resolver and import validation; add independent arrival/registration, eligibility rules, dated accommodation, transport, kits, food, finance and incident modules; add full analytics facts and secure reporting. Full bank collection remains disabled until the restricted boundary is approved. Ordinary SharePoint read access cannot enforce a distinct export deny. If required transactional correctness or security cannot be achieved under Option A, evaluate approved premium Dataverse licensing.

Participants do not get the organiser account or broad list access. Initial assistance is organiser-operated after identity checks. Secure self-service requires separately validated authentication/licensing, such as Power Pages with correct contact-level permissions. Badge/QR generation, reprint history and revocation remain unfinished; never put private records or bank data in QR content.

# Appendix A. Copy-item index

The companion `setup-copy-pack` contains extracted blocks in document order. Open the named text file, replace the documented configuration values, and copy into the EXACT property/action specified above. Do not paste all formulas into App.OnStart.

| Item | Destination |
|---|---|
| GUID generator | Local PowerShell console |
| Pilot stream JSON | deployment/streams.pilot.json |
| Provisioning command | Administrator PowerShell console |
| StartScreen | App.StartScreen |
| Startup configuration | App.OnStart |
| Open participants | btnOpenParticipants.OnSelect |
| Gallery search | galParticipants.Items |
| Edit draft | Gallery Edit draft button.OnSelect |
| New draft | btnNewNomination.OnSelect |
| Category items | ddCategory.Items |
| Save button state | btnSaveDraft.DisplayMode |
| Draft save | btnSaveDraft.OnSelect |
| Cancel | btnCancel.OnSelect |
| Submission request | Gallery template submission button.OnSelect, after flow readiness |
| Trigger condition | Snapshot flow trigger settings |
| Status lookup | Owner gallery status label.Text, after projection readiness |
| Each DAX block | Power BI New measure, one block at a time |

# Appendix B. Reference and verification notes

Repository sources: deployment/DEPLOY.md; sharepoint/core-lists.json; power-apps/Core.fx; power-automate/BUILD.md; power-bi/BUILD.md and measures.dax; tests/TENANT-UAT.md. This guide provides a direct Patch-based draft screen as a separate alternative to the repository's edit-form snippets; use one approach consistently, not both on one Save button.

Relevant Microsoft Learn references (URLs checked during foundation work, not proof of tenant licence rights):

- https://learn.microsoft.com/en-us/power-platform/admin/powerapps-flow-licensing-faq
- https://learn.microsoft.com/en-us/power-apps/maker/canvas-apps/delegation-overview
- https://learn.microsoft.com/en-us/power-apps/maker/canvas-apps/connections/connection-sharepoint-online
- https://learn.microsoft.com/en-us/power-apps/maker/canvas-apps/power-apps-yaml
- https://learn.microsoft.com/en-us/power-pages/security/authentication/

Verification in the build environment: supplied sample CSV totals reconciled; code blocks extracted to plain-text files; document structure and copy-pack contents checked. Power Fx, tenant flows, PnP script, Power BI Desktop and permission behaviour require validation in the actual Microsoft environment. Nothing in this document certifies a production deployment or legal compliance.
