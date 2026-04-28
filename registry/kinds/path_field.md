# path_field

Canonical shared field names whose values locate or reference artifacts, files, URLs, repository paths, output references, source references, reviewed files, or path lists.

Use this kind for fields such as `path`, `repository_path`, `url`, `source_url`, `report_url`, `source_ref`, `source_refs`, `output_dir`, `outputs`, `preview_file`, `allowed_paths`, and `changed_files`.

Rules:

- The row payload is the field/column name and should use `payload_format = field_name` unless a reviewed external contract requires another format.
- Path fields locate or reference something; they do not identify/name the thing itself.
- Use `identity_field` for names, ids, symbols, tickers, issuers, titles, and other identity/naming fields.
- Use `field` for free-text descriptions, metrics, counts, booleans, and structured payload slots that are not locators.
- Use `temporal_field` for date/time values and `classification_field` for controlled vocabulary axes.
