# Designer expression snippets

These are expressions for named actions, not one importable definition. Verify dynamic content names in the tenant designer.

- Submission trigger condition: `@equals(triggerBody()?['SubmitRequested'], true)`
- Correlation: `workflow()?['run']?['name']`
- UTC timestamp: `utcNow()`
- UUID for a new server-side record: `guid()`
- Version-bound receipt: `concat(variables('PartitionListGuid'), ':', string(triggerBody()?['ID']), ':', string(body('Get_item')?['{VersionNumber}']))`
- Outbox key: `concat(variables('RequestKey'), ':', variables('Stage'), ':', variables('Template'), ':', variables('RecipientObjectId'))`

For SharePoint “Send an HTTP request to SharePoint”, an ETag update uses POST to `/_api/web/lists(guid'<LIST-GUID>')/items(<NUMERIC-ID>)`, headers `IF-MATCH: <ETAG FROM GET>`, `X-HTTP-Method: MERGE`, `Accept: application/json;odata=nometadata`, `Content-Type: application/json;odata=nometadata`. Body whitelists only the fields being updated. A stale ETag must return 412 and trigger re-read/conflict handling. Never use `IF-MATCH: *` for capacity or approvals. Insert actual IDs through safe designer parameters; no access tokens are embedded.

Group validation must query trusted group membership and compare the actual SharePoint author/editor identifier, not a client-supplied field. Nested Entra group membership may require capabilities beyond simple SharePoint group enumeration; verify your chosen group design and connector licensing. Fail closed on unresolved membership.
