# Registry kind: parameter_field

Canonical shared field names whose values hold request/task parameter objects, parameter lists, or documented parameter collections.

Use this kind for fields such as `params` and `request_parameters` when the value represents the parameters accepted by a task, source interface, template, or data-kind request contract.

## Boundaries

- Parameter fields describe or carry input/request knobs; they are not ordinary scalar output measurements.
- Use `classification_field` for categorical parameter axes when the field itself is a single normalized category/type/status/scope/tags slot.
- Use `temporal_field` for timestamp/date parameters when the field is a single temporal value.
- Use `identity_field` for identifier/name/symbol parameters when the field is a single identity value.
- Use `text_field` for prose explanations about parameters, not for the parameter collection itself.
- Keep provider raw request names at the ingestion boundary when required by external APIs; normalized project-facing parameter fields should use the registry payload.
- The row payload is the field/column name and should use `payload_format = field_name` unless a reviewed external contract requires another format.
