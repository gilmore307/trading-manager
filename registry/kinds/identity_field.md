# identity_field

Canonical shared field names whose values identify or name an entity, artifact, source, instrument, task, report, or row.

Use this kind for fields such as `id`, `event_id`, `symbol`, `ticker`, `issuer`, `title`, `headline`, `contract_symbol`, `cusip`, and `sedol`.

Rules:

- The row payload is the field/column name and should use `payload_format = field_name` unless the reviewed external contract requires another format.
- Identity fields are not measurements, scores, counts, temporal values, classification axes, paths, URLs, or references.
- Use `path_field` when the value locates or references an artifact, file, URL, repository path, source reference, or output reference.
- Use `classification_field` when the value comes from a controlled vocabulary/classification axis, even if it labels a row.
- Use `temporal_field` when the value is a date/time/timestamp.
- Keep source operational metadata that is not a durable identity/locator in `field`.
