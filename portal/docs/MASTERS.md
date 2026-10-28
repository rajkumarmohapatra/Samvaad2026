# Masters: administrator guide

1. Sign in as the super administrator and select **Masters** in the left menu (or open `/masters/`). Operational users cannot retrieve or edit this area.
2. Select Tribes, Participant categories, Streams/teams/programs, Events, Event editions, or Edition assignments.
3. Search by any text field. On Tribes, filter by state and active/inactive status. Results are paginated, 40 records per page, with full counts.
4. Select **Add record** or **Edit**, enter the fields, and select **Save master**. Invalid codes, duplicates, missing required values and invalid dates produce inline errors.
5. Deactivate unused entries. Deletion is intentionally unavailable from Masters to preserve linked records. Do not rename an edition or reassign its year to reuse it: create a new edition for each year.
6. Follow the Operational masters links for accommodation properties/rooms/beds, vehicles/trips, food locations/windows, kits/inventory, venues/sessions. Existing edition scopes, closed-edition and capacity checks apply there. Roles/permissions remain in privileged Administration.
7. Find saved changes and validation alerts in Notifications, with the acting user, page and IST timestamps.

## Supplied tribe reference

The supplied `Pasted text.txt` has 754 tab-separated rows. Deployment migration 0007 adds these references without overwriting an existing code or participant profile. `SL_National Code` is preserved as the source national-code field; `Tribe Master R3` is preserved as unique_code. The reference is not represented as official legal classification. Tribe name and state spelling are preserved, with surrounding whitespace trimmed. The 15 literal Omitted entries are retained as inactive and cannot be reactivated through Masters. The other 739 entries are initially active. Administrators should review source terminology and codes before operational use.

The optional participant tribe-reference dropdown lists active references. Participant-provided tribe wording remains separate, is never inferred and is not rewritten when a master changes. Existing participant master links remain protected. No automatic matching or reclassification is performed. State fields on participant profiles remain free text; this change does not create an independent geographical master.

Tribe-reference data contains no individual participant identities; only this non-personal source is packaged in migration code. No new dependencies or credentials are required.
