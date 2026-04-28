# classification_field

Canonical shared field names whose values classify, categorize, bucket, label, scope, or otherwise assign a row to a semantic class.

Use this kind for fields such as `event_type`, `source_type`, `impact_scope`, `universe_type`, `exposure_type`, `status`, `kind`, `right`, `sector`, `asset_class`, and other categorical axes.

Rules:

- The row payload is the field/column name and should use `payload_format = field_name`.
- Register the semantic classification axis once, then list every consuming template, receipt, or table in `applies_to`.
- Do not create separate rows only because one template previously used a suffix such as `_hint`, `_event`, or a component prefix.
- Prefer stable lowercase token values for classifications unless a source contract explicitly requires another reviewed encoding.
- Use explicit semantic names:
  - `*_type` for class/type/taxonomy distinctions, including source-provided category labels such as `source_event_type`.
  - `*_status` for state/status slots.
  - `*_scope` for scope/coverage axes.
  - `*_policy`, `*_outcome`, and `*_readiness` only when those words are the actual semantic domain.
  - `*_tags` for multi-label tag sets.
- Avoid vague standalone names such as `category`, `kind`, `type`, or `side_hint` unless they are fixed external/source schema names that cannot be normalized.
- Keep date/time fields in `temporal_field`.
- Keep free-text descriptions, titles, summaries, URLs, numeric metrics, and structured JSON payload slots in `field` unless the value is itself a classification label.
