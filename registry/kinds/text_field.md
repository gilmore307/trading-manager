# Registry kind: text_field

Canonical shared field names whose values are human-readable free-text, narrative notes, explanations, summaries, caveats, diagnostics, errors, or documentation-oriented text columns.

Use this kind for fields such as `summary`, `coverage_reason`, `known_caveats`, `request_parameters`, `acceptance_summary`, `change_summary`, `maintenance_summary`, `task_status_summary`, `error`, and registry `note`.

## Boundaries

- Text fields explain, describe, summarize, or annotate; they are not scalar measurements, identifiers, locators, statuses, temporal values, or classification axes.
- Use `identity_field` for names, ids, symbols, titles/headlines, and other identity/naming fields.
- Use `path_field` for URLs, paths, references, files, and output locators.
- Use `classification_field` for categorical axes and `status_value` for allowed status values.
- Error details belong here when their purpose is diagnostic explanation; status outcomes remain `status_value`.
- Keep structured numeric/model context fields in `field` unless their primary purpose is narrative explanation.
- The row payload is the field/column name and should use `payload_format = field_name` unless a reviewed external contract requires another format.
