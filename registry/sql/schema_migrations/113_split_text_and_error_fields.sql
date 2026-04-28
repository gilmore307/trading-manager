-- Split human-readable narrative/explanatory fields and error fields out of ordinary field.

ALTER TABLE trading_registry DROP CONSTRAINT IF EXISTS trading_registry_kind_check;
ALTER TABLE trading_registry
ADD CONSTRAINT trading_registry_kind_check
CHECK (kind IN (
  'field',
  'identity_field',
  'path_field',
  'temporal_field',
  'classification_field',
  'text_field',
  'error_field',
  'repo',
  'config',
  'term',
  'data_bundle',
  'data_source',
  'source_capability',
  'data_kind',
  'template',
  'shared_artifact',
  'script',
  'payload_format',
  'status_value',
  'artifact_type',
  'manifest_type',
  'ready_signal_type',
  'request_type'
));

UPDATE trading_registry
SET kind = 'text_field',
    note = note || ' Text value explains, describes, summarizes, or annotates rather than measuring, identifying, locating, or classifying.'
WHERE id IN (
  'fld_XYGQ3TIC', -- ACCEPTANCE_SUMMARY / acceptance_summary
  'fld_GNNVKXOG', -- CHANGE_SUMMARY / change_summary
  'fld_EKIND012', -- DATA_KIND_TEMPLATE_KNOWN_CAVEATS / known_caveats
  'fld_EKIND009', -- DATA_KIND_TEMPLATE_REQUEST_PARAMETERS / request_parameters
  'fld_EVT042', -- EVENT_COVERAGE_REASON / coverage_reason
  'fld_37IEP8QF', -- MAINTENANCE_SUMMARY / maintenance_summary
  'fld_D3W7K1RM', -- REGISTRY_ITEM_NOTE / note
  'fld_EVT020', -- SUMMARY / summary
  'fld_W9NA62KA' -- TASK_STATUS_SUMMARY / task_status_summary
);

UPDATE trading_registry
SET kind = 'error_field',
    note = 'per-run error detail; null when run succeeds. Error value carries failure details, diagnostics, exception summaries, or an error payload object.'
WHERE id = 'fld_7FW3A4DF';
