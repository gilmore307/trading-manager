# identity_field

Canonical shared field names whose values identify, name, label, locate, or reference an entity, artifact, source, instrument, task, report, or row.

Use this kind for fields such as `id`, `event_id`, `symbol`, `ticker`, `issuer`, `title`, `headline`, `source_ref`, `url`, `path`, `repository_path`, `contract_symbol`, `cusip`, and `sedol`.

Rules:

- The row payload is the field/column name and should use `payload_format = field_name` unless the reviewed external contract requires another format.
- Identity fields are not measurements, scores, counts, temporal values, or classification axes.
- Use `classification_field` when the value comes from a controlled vocabulary/classification axis, even if it labels a row.
- Use `temporal_field` when the value is a date/time/timestamp.
- Keep source operational metadata that is not a durable identity/locator in `field`.
