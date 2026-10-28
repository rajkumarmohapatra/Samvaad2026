# Badge/QR status and licensing-compatible fallback

QR generation, PDF automation, revocation/reprint workflow and printable native badge layout are **not implemented**. A badge must contain only a random opaque token and approved display details, never contact, banking, document numbers or internal approval remarks. A scan must still authenticate the operator before it retrieves a record. Tokens must be revocable; they are not participant login credentials.

For a standard-connector pilot, use a simple organizer-printed badge with name, event edition, stream and human-readable opaque reference, after registration approval. Use an approved local Office template and print through an authorized workstation; do not send personal data to a public QR website. QR can be added only after evaluating a vetted locally bundled encoder/PCF control or an approved Microsoft-hosted QR service and its licensing/security implications. Power Apps barcode reader support does not imply QR generation support.

Word Online template actions and automated PDF conversions have connector/action-specific licensing and limitations; confirm in the tenant before selecting them. Browser/manual printing may avoid a premium PDF connector but does not deliver an automated issuance/reprint audit. That audit and approved print layout remain a Phase 2 gate.
