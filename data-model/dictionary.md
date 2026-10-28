# Data dictionary
Logical design: **not all entities are provisioned or implemented**. RecordKey is the application GUID; SharePoint also has its own numeric ID. Cross-list references require service validation. No cascaded deletion.

## Events
Boundary: Configuration. Retention: Keep event configuration and immutable yearly labels; annual review.

| Field | Type | Required | Indexed | Unique |
|---|---|---|---|---|
| RecordKey | guid | True | True | True |
| CreatedAt | datetime | True | False | False |
| UpdatedAt | datetime | True | False | False |
| EventCode | text | True | False | False |
| Name | text | True | False | False |
| Active | boolean | True | False | False |

GUID references must exist; edition references must agree; immutable annual snapshots; domain rules in requirements/invariants.md.

## EventEditions
Boundary: Configuration. Retention: Keep event configuration and immutable yearly labels; annual review.

| Field | Type | Required | Indexed | Unique |
|---|---|---|---|---|
| RecordKey | guid | True | True | True |
| CreatedAt | datetime | True | False | False |
| UpdatedAt | datetime | True | False | False |
| EditionCode | text | True | True | True |
| EventId | guid | True | True | False |
| Year | integer | True | False | False |
| Starts | date | True | False | False |
| Ends | date | True | False | False |
| Status | text | True | True | False |
| ClosedAt | datetime | False | False | False |

GUID references must exist; edition references must agree; immutable annual snapshots; domain rules in requirements/invariants.md.

## OrganizationalUnits
Boundary: Configuration. Retention: Keep event configuration and immutable yearly labels; annual review.

| Field | Type | Required | Indexed | Unique |
|---|---|---|---|---|
| RecordKey | guid | True | True | True |
| CreatedAt | datetime | True | False | False |
| UpdatedAt | datetime | True | False | False |
| UnitCode | text | True | False | False |
| Name | text | True | False | False |
| Kind | text | True | False | False |
| Active | boolean | True | False | False |
| MergedInto | guid | False | False | False |

GUID references must exist; edition references must agree; immutable annual snapshots; domain rules in requirements/invariants.md.

## EditionUnits
Boundary: Configuration. Retention: Keep event configuration and immutable yearly labels; annual review.

| Field | Type | Required | Indexed | Unique |
|---|---|---|---|---|
| RecordKey | guid | True | True | True |
| CreatedAt | datetime | True | False | False |
| UpdatedAt | datetime | True | False | False |
| EditionId | guid | True | True | False |
| UnitId | guid | True | True | False |
| DisplayNameSnapshot | text | True | False | False |
| OwnerGroupId | integer | True | True | False |
| Active | boolean | True | False | False |

GUID references must exist; edition references must agree; immutable annual snapshots; domain rules in requirements/invariants.md.

## Streams
Boundary: Configuration. Retention: Keep event configuration and immutable yearly labels; annual review.

| Field | Type | Required | Indexed | Unique |
|---|---|---|---|---|
| RecordKey | guid | True | True | True |
| CreatedAt | datetime | True | False | False |
| UpdatedAt | datetime | True | False | False |
| UnitId | guid | True | True | False |
| Description | memo | False | False | False |

GUID references must exist; edition references must agree; immutable annual snapshots; domain rules in requirements/invariants.md.

## Teams
Boundary: Configuration. Retention: Keep event configuration and immutable yearly labels; annual review.

| Field | Type | Required | Indexed | Unique |
|---|---|---|---|---|
| RecordKey | guid | True | True | True |
| CreatedAt | datetime | True | False | False |
| UpdatedAt | datetime | True | False | False |
| UnitId | guid | True | True | False |
| Responsibility | memo | False | False | False |

GUID references must exist; edition references must agree; immutable annual snapshots; domain rules in requirements/invariants.md.

## TeamResponsibilities
Boundary: Configuration. Retention: Keep event configuration and immutable yearly labels; annual review.

| Field | Type | Required | Indexed | Unique |
|---|---|---|---|---|
| RecordKey | guid | True | True | True |
| CreatedAt | datetime | True | False | False |
| UpdatedAt | datetime | True | False | False |
| EditionId | guid | True | True | False |
| TeamId | guid | True | True | False |
| UnitId | guid | True | True | False |
| Responsibility | text | True | False | False |

GUID references must exist; edition references must agree; immutable annual snapshots; domain rules in requirements/invariants.md.

## Venues
Boundary: Operations. Retention: Review after event; duration requires approved records schedule and hold policy.

| Field | Type | Required | Indexed | Unique |
|---|---|---|---|---|
| RecordKey | guid | True | True | True |
| CreatedAt | datetime | True | False | False |
| UpdatedAt | datetime | True | False | False |
| EditionId | guid | True | True | False |
| Name | text | True | False | False |
| Capacity | integer | True | False | False |
| Address | memo | False | False | False |
| Accessible | boolean | True | False | False |

GUID references must exist; edition references must agree; immutable annual snapshots; domain rules in requirements/invariants.md.

## ActivityLocations
Boundary: Operations. Retention: Review after event; duration requires approved records schedule and hold policy.

| Field | Type | Required | Indexed | Unique |
|---|---|---|---|---|
| RecordKey | guid | True | True | True |
| CreatedAt | datetime | True | False | False |
| UpdatedAt | datetime | True | False | False |
| VenueId | guid | True | True | False |
| Name | text | True | False | False |
| Capacity | integer | True | False | False |

GUID references must exist; edition references must agree; immutable annual snapshots; domain rules in requirements/invariants.md.

## Sessions
Boundary: Operations. Retention: Review after event; duration requires approved records schedule and hold policy.

| Field | Type | Required | Indexed | Unique |
|---|---|---|---|---|
| RecordKey | guid | True | True | True |
| CreatedAt | datetime | True | False | False |
| UpdatedAt | datetime | True | False | False |
| EditionId | guid | True | True | False |
| LocationId | guid | True | True | False |
| StreamId | guid | True | True | False |
| Title | text | True | False | False |
| Starts | datetime | True | False | False |
| Ends | datetime | True | False | False |
| CoordinatorId | text | True | True | False |
| Capacity | integer | True | False | False |

GUID references must exist; edition references must agree; immutable annual snapshots; domain rules in requirements/invariants.md.

## SessionAssignments
Boundary: Operations. Retention: Review after event; duration requires approved records schedule and hold policy.

| Field | Type | Required | Indexed | Unique |
|---|---|---|---|---|
| RecordKey | guid | True | True | True |
| CreatedAt | datetime | True | False | False |
| UpdatedAt | datetime | True | False | False |
| SessionId | guid | True | True | False |
| ParticipationId | guid | True | True | False |
| AttendanceStatus | text | True | False | False |
| AttendedAt | datetime | False | False | False |

GUID references must exist; edition references must agree; immutable annual snapshots; domain rules in requirements/invariants.md.

## Participants
Boundary: RestrictedProfile. Retention: Review after event; retain reusable profile only under documented purpose and notice.

| Field | Type | Required | Indexed | Unique |
|---|---|---|---|---|
| RecordKey | guid | True | True | True |
| CreatedAt | datetime | True | False | False |
| UpdatedAt | datetime | True | False | False |
| FullName | text | True | False | False |
| PreferredName | text | False | False | False |
| Phone | text | True | False | False |
| AlternatePhone | text | False | False | False |
| Email | text | False | False | False |
| State | text | True | False | False |
| District | text | False | False | False |
| Village | text | False | False | False |
| Community | memo | False | False | False |
| Languages | memo | False | False | False |
| Gender | text | False | False | False |
| BirthDate | date | False | False | False |
| IdentityType | text | False | False | False |
| IdentityStatus | text | True | False | False |

GUID references must exist; edition references must agree; immutable annual snapshots; domain rules in requirements/invariants.md.

## EventParticipations
Boundary: Operations. Retention: Review after event; duration requires approved records schedule and hold policy.

| Field | Type | Required | Indexed | Unique |
|---|---|---|---|---|
| RecordKey | guid | True | True | True |
| CreatedAt | datetime | True | False | False |
| UpdatedAt | datetime | True | False | False |
| ParticipantId | guid | True | True | False |
| EditionId | guid | True | True | False |
| PrimaryStreamId | guid | True | True | False |
| Category | text | True | False | False |
| NominatingTeamId | guid | True | True | False |
| OwnerId | text | True | True | False |
| Starts | date | True | False | False |
| Ends | date | True | False | False |
| ReviewStatus | text | True | False | False |
| TravelEligible | boolean | True | False | False |
| AccommodationEligible | boolean | True | False | False |
| FoodEligible | boolean | True | False | False |
| KitEligible | boolean | True | False | False |
| FinanceEligible | boolean | True | False | False |
| ArrivalStatus | text | True | False | False |
| RegistrationStatus | text | True | False | False |
| DepartureStatus | text | True | False | False |
| OpaqueBadgeToken | guid | True | False | False |

GUID references must exist; edition references must agree; immutable annual snapshots; domain rules in requirements/invariants.md.

## ParticipationSnapshots
Boundary: Operations. Retention: Review after event; duration requires approved records schedule and hold policy.

| Field | Type | Required | Indexed | Unique |
|---|---|---|---|---|
| RecordKey | guid | True | True | True |
| CreatedAt | datetime | True | False | False |
| UpdatedAt | datetime | True | False | False |
| ParticipationId | guid | True | True | False |
| NominationRecordKey | guid | True | True | False |
| EditionId | guid | True | True | False |
| DisplayName | text | True | False | False |
| StreamNameSnapshot | text | True | False | False |
| CategorySnapshot | text | True | False | False |
| ReviewStatus | text | True | False | False |
| SourceVersion | integer | True | False | False |

GUID references must exist; edition references must agree; immutable annual snapshots; domain rules in requirements/invariants.md.

## ParticipantStreamAssignments
Boundary: Operations. Retention: Review after event; duration requires approved records schedule and hold policy.

| Field | Type | Required | Indexed | Unique |
|---|---|---|---|---|
| RecordKey | guid | True | True | True |
| CreatedAt | datetime | True | False | False |
| UpdatedAt | datetime | True | False | False |
| ParticipationId | guid | True | True | False |
| StreamId | guid | True | True | False |
| IsPrimary | boolean | True | False | False |

GUID references must exist; edition references must agree; immutable annual snapshots; domain rules in requirements/invariants.md.

## Nominations
Boundary: StreamPartition. Retention: Review after event; duration requires approved records schedule and hold policy.

| Field | Type | Required | Indexed | Unique |
|---|---|---|---|---|
| RecordKey | guid | True | True | True |
| CreatedAt | datetime | True | False | False |
| UpdatedAt | datetime | True | False | False |
| EditionId | guid | True | True | False |
| StreamId | guid | True | True | False |
| FullName | text | True | False | False |
| Phone | text | True | False | False |
| State | text | True | False | False |
| District | text | False | False | False |
| Community | memo | False | False | False |
| Category | text | True | False | False |
| ClientRequestKey | guid | True | True | True |
| SubmitRequested | boolean | True | False | False |

GUID references must exist; edition references must agree; immutable annual snapshots; domain rules in requirements/invariants.md.

## ReviewQueue
Boundary: Reviewer. Retention: Review after event; duration requires approved records schedule and hold policy.

| Field | Type | Required | Indexed | Unique |
|---|---|---|---|---|
| RecordKey | guid | True | True | True |
| CreatedAt | datetime | True | False | False |
| UpdatedAt | datetime | True | False | False |
| NominationKey | text | True | True | True |
| EditionId | guid | True | True | False |
| StreamId | guid | True | True | False |
| SourceVersion | text | True | False | False |
| Snapshot | memo | True | False | False |
| Status | text | True | True | False |
| ReviewerId | text | False | True | False |
| ReviewedAt | datetime | False | False | False |
| RejectionReason | memo | False | False | False |

GUID references must exist; edition references must agree; immutable annual snapshots; domain rules in requirements/invariants.md.

## TravelBookings
Boundary: Transport. Retention: Review after event; duration requires approved records schedule and hold policy.

| Field | Type | Required | Indexed | Unique |
|---|---|---|---|---|
| RecordKey | guid | True | True | True |
| CreatedAt | datetime | True | False | False |
| UpdatedAt | datetime | True | False | False |
| ParticipationId | guid | True | True | False |
| Mode | text | True | False | False |
| Origin | text | True | False | False |
| ArrivalAt | datetime | False | False | False |
| DepartureAt | datetime | False | False | False |
| ServiceNumber | text | False | False | False |
| PickupPoint | text | False | False | False |
| BookingReference | text | False | False | False |
| Status | text | True | True | False |

GUID references must exist; edition references must agree; immutable annual snapshots; domain rules in requirements/invariants.md.

## Vehicles
Boundary: Transport. Retention: Review after event; duration requires approved records schedule and hold policy.

| Field | Type | Required | Indexed | Unique |
|---|---|---|---|---|
| RecordKey | guid | True | True | True |
| CreatedAt | datetime | True | False | False |
| UpdatedAt | datetime | True | False | False |
| EditionId | guid | True | True | False |
| Registration | text | True | False | False |
| Capacity | integer | True | False | False |
| DriverName | text | True | False | False |
| DriverPhone | text | True | False | False |
| CoordinatorId | text | True | True | False |

GUID references must exist; edition references must agree; immutable annual snapshots; domain rules in requirements/invariants.md.

## Trips
Boundary: Transport. Retention: Review after event; duration requires approved records schedule and hold policy.

| Field | Type | Required | Indexed | Unique |
|---|---|---|---|---|
| RecordKey | guid | True | True | True |
| CreatedAt | datetime | True | False | False |
| UpdatedAt | datetime | True | False | False |
| EditionId | guid | True | True | False |
| VehicleId | guid | True | True | False |
| Origin | text | True | False | False |
| Destination | text | True | False | False |
| Starts | datetime | True | False | False |
| Ends | datetime | True | False | False |
| Status | text | True | True | False |

GUID references must exist; edition references must agree; immutable annual snapshots; domain rules in requirements/invariants.md.

## TripPassengers
Boundary: Transport. Retention: Review after event; duration requires approved records schedule and hold policy.

| Field | Type | Required | Indexed | Unique |
|---|---|---|---|---|
| RecordKey | guid | True | True | True |
| CreatedAt | datetime | True | False | False |
| UpdatedAt | datetime | True | False | False |
| TripId | guid | True | True | False |
| ParticipationId | guid | True | True | False |
| Status | text | True | True | False |

GUID references must exist; edition references must agree; immutable annual snapshots; domain rules in requirements/invariants.md.

## AccommodationProperties
Boundary: Accommodation. Retention: Review after event; duration requires approved records schedule and hold policy.

| Field | Type | Required | Indexed | Unique |
|---|---|---|---|---|
| RecordKey | guid | True | True | True |
| CreatedAt | datetime | True | False | False |
| UpdatedAt | datetime | True | False | False |
| EditionId | guid | True | True | False |
| Name | text | True | False | False |
| Address | memo | True | False | False |
| Contact | text | False | False | False |

GUID references must exist; edition references must agree; immutable annual snapshots; domain rules in requirements/invariants.md.

## Buildings
Boundary: Accommodation. Retention: Review after event; duration requires approved records schedule and hold policy.

| Field | Type | Required | Indexed | Unique |
|---|---|---|---|---|
| RecordKey | guid | True | True | True |
| CreatedAt | datetime | True | False | False |
| UpdatedAt | datetime | True | False | False |
| PropertyId | guid | True | True | False |
| Name | text | True | False | False |

GUID references must exist; edition references must agree; immutable annual snapshots; domain rules in requirements/invariants.md.

## Rooms
Boundary: Accommodation. Retention: Review after event; duration requires approved records schedule and hold policy.

| Field | Type | Required | Indexed | Unique |
|---|---|---|---|---|
| RecordKey | guid | True | True | True |
| CreatedAt | datetime | True | False | False |
| UpdatedAt | datetime | True | False | False |
| BuildingId | guid | True | True | False |
| Name | text | True | False | False |
| Capacity | integer | True | False | False |
| Restriction | text | True | False | False |
| Accessible | boolean | True | False | False |

GUID references must exist; edition references must agree; immutable annual snapshots; domain rules in requirements/invariants.md.

## Beds
Boundary: Accommodation. Retention: Review after event; duration requires approved records schedule and hold policy.

| Field | Type | Required | Indexed | Unique |
|---|---|---|---|---|
| RecordKey | guid | True | True | True |
| CreatedAt | datetime | True | False | False |
| UpdatedAt | datetime | True | False | False |
| RoomId | guid | True | True | False |
| EditionId | guid | True | True | False |
| Label | text | True | False | False |
| Active | boolean | True | False | False |

GUID references must exist; edition references must agree; immutable annual snapshots; domain rules in requirements/invariants.md.

## AccommodationAllocations
Boundary: Accommodation. Retention: Review after event; duration requires approved records schedule and hold policy.

| Field | Type | Required | Indexed | Unique |
|---|---|---|---|---|
| RecordKey | guid | True | True | True |
| CreatedAt | datetime | True | False | False |
| UpdatedAt | datetime | True | False | False |
| ParticipationId | guid | True | True | False |
| BedId | guid | True | True | False |
| Starts | datetime | True | False | False |
| Ends | datetime | True | False | False |
| Status | text | True | True | False |
| CheckedInAt | datetime | False | False | False |
| CheckedOutAt | datetime | False | False | False |
| AllocationKey | text | True | True | True |

GUID references must exist; edition references must agree; immutable annual snapshots; domain rules in requirements/invariants.md.

## MealLocations
Boundary: Food. Retention: Review after event; duration requires approved records schedule and hold policy.

| Field | Type | Required | Indexed | Unique |
|---|---|---|---|---|
| RecordKey | guid | True | True | True |
| CreatedAt | datetime | True | False | False |
| UpdatedAt | datetime | True | False | False |
| EditionId | guid | True | True | False |
| Name | text | True | False | False |
| Capacity | integer | True | False | False |

GUID references must exist; edition references must agree; immutable annual snapshots; domain rules in requirements/invariants.md.

## FoodStalls
Boundary: Food. Retention: Review after event; duration requires approved records schedule and hold policy.

| Field | Type | Required | Indexed | Unique |
|---|---|---|---|---|
| RecordKey | guid | True | True | True |
| CreatedAt | datetime | True | False | False |
| UpdatedAt | datetime | True | False | False |
| LocationId | guid | True | True | False |
| Name | text | True | False | False |
| Cuisine | text | False | False | False |
| Capacity | integer | True | False | False |

GUID references must exist; edition references must agree; immutable annual snapshots; domain rules in requirements/invariants.md.

## MealWindows
Boundary: Food. Retention: Review after event; duration requires approved records schedule and hold policy.

| Field | Type | Required | Indexed | Unique |
|---|---|---|---|---|
| RecordKey | guid | True | True | True |
| CreatedAt | datetime | True | False | False |
| UpdatedAt | datetime | True | False | False |
| EditionId | guid | True | True | False |
| LocationId | guid | True | True | False |
| Starts | datetime | True | False | False |
| Ends | datetime | True | False | False |
| Capacity | integer | True | False | False |

GUID references must exist; edition references must agree; immutable annual snapshots; domain rules in requirements/invariants.md.

## MealEntitlements
Boundary: Food. Retention: Review after event; duration requires approved records schedule and hold policy.

| Field | Type | Required | Indexed | Unique |
|---|---|---|---|---|
| RecordKey | guid | True | True | True |
| CreatedAt | datetime | True | False | False |
| UpdatedAt | datetime | True | False | False |
| ParticipationId | guid | True | True | False |
| WindowId | guid | True | True | False |
| Quantity | integer | True | False | False |
| DietaryInstructions | memo | False | False | False |

GUID references must exist; edition references must agree; immutable annual snapshots; domain rules in requirements/invariants.md.

## MealTransactions
Boundary: Food. Retention: Review after event; duration requires approved records schedule and hold policy.

| Field | Type | Required | Indexed | Unique |
|---|---|---|---|---|
| RecordKey | guid | True | True | True |
| CreatedAt | datetime | True | False | False |
| UpdatedAt | datetime | True | False | False |
| ParticipationId | guid | True | True | False |
| WindowId | guid | True | True | False |
| Quantity | integer | True | False | False |
| ServedAt | datetime | True | False | False |
| IssueKey | text | True | True | True |

GUID references must exist; edition references must agree; immutable annual snapshots; domain rules in requirements/invariants.md.

## KitInventory
Boundary: Kits. Retention: Review after event; duration requires approved records schedule and hold policy.

| Field | Type | Required | Indexed | Unique |
|---|---|---|---|---|
| RecordKey | guid | True | True | True |
| CreatedAt | datetime | True | False | False |
| UpdatedAt | datetime | True | False | False |
| EditionId | guid | True | True | False |
| Kind | text | True | False | False |
| Movement | text | True | False | False |
| Quantity | integer | True | False | False |
| Reference | text | True | False | False |
| RecordedAt | datetime | True | False | False |

GUID references must exist; edition references must agree; immutable annual snapshots; domain rules in requirements/invariants.md.

## KitAllocations
Boundary: Kits. Retention: Review after event; duration requires approved records schedule and hold policy.

| Field | Type | Required | Indexed | Unique |
|---|---|---|---|---|
| RecordKey | guid | True | True | True |
| CreatedAt | datetime | True | False | False |
| UpdatedAt | datetime | True | False | False |
| ParticipationId | guid | True | True | False |
| Kind | text | True | False | False |
| Quantity | integer | True | False | False |

GUID references must exist; edition references must agree; immutable annual snapshots; domain rules in requirements/invariants.md.

## KitIssues
Boundary: Kits. Retention: Review after event; duration requires approved records schedule and hold policy.

| Field | Type | Required | Indexed | Unique |
|---|---|---|---|---|
| RecordKey | guid | True | True | True |
| CreatedAt | datetime | True | False | False |
| UpdatedAt | datetime | True | False | False |
| ParticipationId | guid | True | True | False |
| Kind | text | True | False | False |
| IssueKey | text | True | True | True |
| IssuedAt | datetime | True | False | False |
| Reason | text | True | False | False |
| ReplacesIssueId | guid | False | True | False |

GUID references must exist; edition references must agree; immutable annual snapshots; domain rules in requirements/invariants.md.

## IdentityVerification
Boundary: Identity. Retention: Do not collect document copies by default. Verification status preferred; delete reference after approved purpose ends.

| Field | Type | Required | Indexed | Unique |
|---|---|---|---|---|
| RecordKey | guid | True | True | True |
| CreatedAt | datetime | True | False | False |
| UpdatedAt | datetime | True | False | False |
| ParticipationId | guid | True | True | False |
| DocumentType | text | True | False | False |
| Status | text | True | True | False |
| DocumentReference | text | False | False | False |
| VerifiedBy | text | False | False | False |
| VerifiedAt | datetime | False | False | False |

GUID references must exist; edition references must agree; immutable annual snapshots; domain rules in requirements/invariants.md.

## EmergencyAssistance
Boundary: Safety. Retention: Short purpose-bound period approved by privacy lead; review immediately after event.

| Field | Type | Required | Indexed | Unique |
|---|---|---|---|---|
| RecordKey | guid | True | True | True |
| CreatedAt | datetime | True | False | False |
| UpdatedAt | datetime | True | False | False |
| ParticipationId | guid | True | True | False |
| EmergencyContact | text | False | False | False |
| AccessibilityInstructions | memo | False | False | False |
| AssistanceInstructions | memo | False | False | False |
| ReviewAt | date | True | False | False |

GUID references must exist; edition references must agree; immutable annual snapshots; domain rules in requirements/invariants.md.

## RestrictedBankDetails
Boundary: FinanceVault. Retention: Policy decision required before use; delete after approved finance/legal retention and hold review.

| Field | Type | Required | Indexed | Unique |
|---|---|---|---|---|
| RecordKey | guid | True | True | True |
| CreatedAt | datetime | True | False | False |
| UpdatedAt | datetime | True | False | False |
| ParticipantId | guid | True | True | False |
| AccountHolder | text | True | False | False |
| BankName | text | True | False | False |
| AccountNumber | text | True | False | False |
| IFSC | text | True | False | False |
| VerificationStatus | text | True | False | False |
| VerifiedBy | text | False | False | False |
| VerifiedAt | datetime | False | False | False |
| ReviewAt | date | True | False | False |

GUID references must exist; edition references must agree; immutable annual snapshots; domain rules in requirements/invariants.md.

## FinancialRequests
Boundary: Finance. Retention: Review after event; duration requires approved records schedule and hold policy.

| Field | Type | Required | Indexed | Unique |
|---|---|---|---|---|
| RecordKey | guid | True | True | True |
| CreatedAt | datetime | True | False | False |
| UpdatedAt | datetime | True | False | False |
| ParticipationId | guid | True | True | False |
| Category | text | True | False | False |
| EligiblePaise | integer | True | False | False |
| RequestedPaise | integer | True | False | False |
| ApprovedPaise | integer | True | False | False |
| MakerId | text | True | True | False |
| Status | text | True | True | False |

GUID references must exist; edition references must agree; immutable annual snapshots; domain rules in requirements/invariants.md.

## FinancialApprovals
Boundary: FinanceChecker. Retention: Review after event; duration requires approved records schedule and hold policy.

| Field | Type | Required | Indexed | Unique |
|---|---|---|---|---|
| RecordKey | guid | True | True | True |
| CreatedAt | datetime | True | False | False |
| UpdatedAt | datetime | True | False | False |
| RequestId | guid | True | True | False |
| Stage | text | True | False | False |
| Decision | text | True | False | False |
| ApproverId | text | True | True | False |
| DecidedAt | datetime | True | False | False |
| RequestVersion | text | True | False | False |

GUID references must exist; edition references must agree; immutable annual snapshots; domain rules in requirements/invariants.md.

## PaymentRecords
Boundary: FinancePayer. Retention: Review after event; duration requires approved records schedule and hold policy.

| Field | Type | Required | Indexed | Unique |
|---|---|---|---|---|
| RecordKey | guid | True | True | True |
| CreatedAt | datetime | True | False | False |
| UpdatedAt | datetime | True | False | False |
| RequestId | guid | True | True | False |
| AmountPaise | integer | True | False | False |
| Status | text | True | True | False |
| ExternalReference | text | False | False | False |
| RecordedAt | datetime | True | False | False |
| RecordedBy | text | True | False | False |
| ReconciledAt | datetime | False | False | False |

GUID references must exist; edition references must agree; immutable annual snapshots; domain rules in requirements/invariants.md.

## BadgeIssues
Boundary: Registration. Retention: Review after event; duration requires approved records schedule and hold policy.

| Field | Type | Required | Indexed | Unique |
|---|---|---|---|---|
| RecordKey | guid | True | True | True |
| CreatedAt | datetime | True | False | False |
| UpdatedAt | datetime | True | False | False |
| ParticipationId | guid | True | True | False |
| OpaqueToken | guid | True | False | False |
| IssuedAt | datetime | True | False | False |
| Reason | text | True | False | False |
| RevokedAt | datetime | False | False | False |
| ReplacesId | guid | False | True | False |

GUID references must exist; edition references must agree; immutable annual snapshots; domain rules in requirements/invariants.md.

## UserRoles
Boundary: SecurityAdmin. Retention: Review after event; duration requires approved records schedule and hold policy.

| Field | Type | Required | Indexed | Unique |
|---|---|---|---|---|
| RecordKey | guid | True | True | True |
| CreatedAt | datetime | True | False | False |
| UpdatedAt | datetime | True | False | False |
| EntraObjectId | text | True | True | False |
| RoleId | text | True | True | False |
| EditionId | guid | True | True | False |
| StreamId | guid | False | True | False |
| ValidUntil | datetime | True | False | False |

GUID references must exist; edition references must agree; immutable annual snapshots; domain rules in requirements/invariants.md.

## RolePermissions
Boundary: SecurityAdmin. Retention: Review after event; duration requires approved records schedule and hold policy.

| Field | Type | Required | Indexed | Unique |
|---|---|---|---|---|
| RecordKey | guid | True | True | True |
| CreatedAt | datetime | True | False | False |
| UpdatedAt | datetime | True | False | False |
| RoleId | text | True | True | False |
| Resource | text | True | False | False |
| CanView | boolean | True | False | False |
| CanCreate | boolean | True | False | False |
| CanEdit | boolean | True | False | False |
| CanApprove | boolean | True | False | False |
| CanExport | boolean | True | False | False |
| CanDelete | boolean | True | False | False |

GUID references must exist; edition references must agree; immutable annual snapshots; domain rules in requirements/invariants.md.

## HelpdeskTickets
Boundary: Helpdesk. Retention: Review after event; duration requires approved records schedule and hold policy.

| Field | Type | Required | Indexed | Unique |
|---|---|---|---|---|
| RecordKey | guid | True | True | True |
| CreatedAt | datetime | True | False | False |
| UpdatedAt | datetime | True | False | False |
| EditionId | guid | True | True | False |
| ParticipationId | guid | False | True | False |
| Category | text | True | False | False |
| Priority | text | True | False | False |
| OwnerId | text | True | True | False |
| Status | text | True | True | False |
| Summary | memo | True | False | False |
| DueAt | datetime | False | False | False |
| ResolvedAt | datetime | False | False | False |

GUID references must exist; edition references must agree; immutable annual snapshots; domain rules in requirements/invariants.md.

## RestrictedIncidents
Boundary: Safety. Retention: Short purpose-bound period approved by privacy lead; review immediately after event.

| Field | Type | Required | Indexed | Unique |
|---|---|---|---|---|
| RecordKey | guid | True | True | True |
| CreatedAt | datetime | True | False | False |
| UpdatedAt | datetime | True | False | False |
| EditionId | guid | True | True | False |
| ParticipationId | guid | False | True | False |
| Category | text | True | False | False |
| Priority | text | True | False | False |
| OwnerId | text | True | True | False |
| Status | text | True | True | False |
| Details | memo | True | False | False |
| ReviewAt | date | True | False | False |

GUID references must exist; edition references must agree; immutable annual snapshots; domain rules in requirements/invariants.md.

## ApprovalHistory
Boundary: Audit. Retention: Approved audit schedule; lock exports and hold exceptions.

| Field | Type | Required | Indexed | Unique |
|---|---|---|---|---|
| RecordKey | guid | True | True | True |
| CreatedAt | datetime | True | False | False |
| UpdatedAt | datetime | True | False | False |
| ParticipationId | guid | True | True | False |
| Workflow | text | True | False | False |
| Stage | text | True | False | False |
| ActorObjectId | text | True | True | False |
| Decision | text | True | False | False |
| At | datetime | True | False | False |
| RequestKey | text | True | True | True |
| Notes | memo | False | False | False |

GUID references must exist; edition references must agree; immutable annual snapshots; domain rules in requirements/invariants.md.

## AuditEvents
Boundary: Audit. Retention: Approved audit schedule; lock exports and hold exceptions.

| Field | Type | Required | Indexed | Unique |
|---|---|---|---|---|
| RecordKey | guid | True | True | True |
| CreatedAt | datetime | True | False | False |
| UpdatedAt | datetime | True | False | False |
| EditionId | guid | True | True | False |
| EntityName | text | True | False | False |
| EntityId | guid | True | True | False |
| Action | text | True | False | False |
| ActorObjectId | text | True | True | False |
| At | datetime | True | False | False |
| CorrelationId | text | True | True | False |
| Outcome | text | True | False | False |

GUID references must exist; edition references must agree; immutable annual snapshots; domain rules in requirements/invariants.md.

## CommandQueue
Boundary: Automation. Retention: Review after event; duration requires approved records schedule and hold policy.

| Field | Type | Required | Indexed | Unique |
|---|---|---|---|---|
| RecordKey | guid | True | True | True |
| CreatedAt | datetime | True | False | False |
| UpdatedAt | datetime | True | False | False |
| EditionId | guid | True | True | False |
| EntityId | guid | True | True | False |
| Action | text | True | False | False |
| ExpectedVersion | text | True | False | False |
| RequestKey | text | True | True | True |
| Status | text | True | True | False |
| Attempt | integer | True | False | False |
| NextAttemptAt | datetime | False | False | False |
| ErrorCode | text | False | False | False |

GUID references must exist; edition references must agree; immutable annual snapshots; domain rules in requirements/invariants.md.

## WorkflowReceipts
Boundary: Automation. Retention: Review after event; duration requires approved records schedule and hold policy.

| Field | Type | Required | Indexed | Unique |
|---|---|---|---|---|
| RecordKey | guid | True | True | True |
| CreatedAt | datetime | True | False | False |
| UpdatedAt | datetime | True | False | False |
| RequestKey | text | True | True | True |
| Stage | text | True | False | False |
| State | text | True | False | False |
| TargetId | text | False | True | False |
| SourceVersion | text | True | False | False |
| LeaseUntil | datetime | False | False | False |
| LastErrorCode | text | False | False | False |

GUID references must exist; edition references must agree; immutable annual snapshots; domain rules in requirements/invariants.md.

## NotificationOutbox
Boundary: Automation. Retention: Review after event; duration requires approved records schedule and hold policy.

| Field | Type | Required | Indexed | Unique |
|---|---|---|---|---|
| RecordKey | guid | True | True | True |
| CreatedAt | datetime | True | False | False |
| UpdatedAt | datetime | True | False | False |
| DedupeKey | text | True | True | True |
| Template | text | True | False | False |
| RecipientObjectId | text | True | True | False |
| State | text | True | False | False |
| Attempts | integer | True | False | False |
| SentAt | datetime | False | False | False |

GUID references must exist; edition references must agree; immutable annual snapshots; domain rules in requirements/invariants.md.
