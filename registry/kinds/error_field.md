# Registry kind: error_field

Canonical shared field names whose values carry error details, failure diagnostics, exception summaries, or error payload objects.

Use this kind for fields such as `error` when a task, run, request, source probe, or pipeline output records failure details.

## Boundaries

- Error fields describe failures or diagnostics; they are not ordinary narrative notes and not status axes.
- Use `status_value` domains for allowed status values such as `failed`, `blocked`, or `succeeded`.
- Use `text_field` for non-error explanations, summaries, notes, caveats, and reason strings.
- Use `field` for ordinary numeric/object payloads whose primary meaning is not failure reporting.
- The row payload is the field/column name and should use `payload_format = field_name` unless a reviewed external contract requires another format.
