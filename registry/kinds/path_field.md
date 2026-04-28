# path_field

Canonical shared field names whose values locate or reference artifacts, files, URLs, repository paths, output references, source references, reviewed files, or path lists.

Use this kind for locator/reference fields such as `registry_item_path`, `repository_path`, `data_task_run_output_directory`, `data_task_run_output_references`, `event_reference`, `execution_allowed_paths`, and `completion_changed_file_paths`.

Rules:

- The row payload is the field/column name and should use `payload_format = field_name` unless a reviewed external contract requires another format.
- Use a single-name payload only for genuinely generic shared locators; scoped locators should use prefix + semantic suffix, such as `registry_item_path`, `event_link_url`, `source_reference`, `source_references`, or `data_task_run_output_directory`.
- Path fields locate or reference something; they do not identify/name the thing itself.
- Use `identity_field` for names, ids, symbols, tickers, issuers, titles, and other identity/naming fields.
- Use `field` for free-text descriptions, metrics, counts, booleans, and structured payload slots that are not locators.
- Use `temporal_field` for date/time values and `classification_field` for controlled vocabulary axes.
