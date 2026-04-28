# classification_field

Canonical shared field names whose values classify, categorize, bucket, label, scope, or otherwise assign a row to a semantic class.

Use this kind for fields such as `event_type`, `source_type`, `impact_scope`, `universe_type`, `exposure_type`, `option_right_type`, `sector_type`, `asset_class`, and other categorical axes.

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
  - `kind` only for registry-native schema terms such as `data_kind` or `registry_item_kind`; otherwise prefer `*_type`.
- Avoid vague standalone names such as `category`, `kind`, `type`, `right`, or `side_hint` unless they are fixed external/source schema names that cannot be normalized.
- Keep date/time fields in `temporal_field`.
- Keep identifiers, names, titles, URLs, paths, and references in `identity_field`.
- Keep free-text descriptions, summaries, numeric metrics, and structured JSON payload slots in `field` unless the value is itself a classification label.
