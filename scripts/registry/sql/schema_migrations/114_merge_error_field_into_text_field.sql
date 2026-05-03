-- Merge error fields into text_field; error details are diagnostic text/payload explanations.

UPDATE trading_registry
SET kind = 'text_field',
    note = 'per-run error detail; null when run succeeds. Text value carries failure details, diagnostics, exception summaries, or an error payload object.'
WHERE id = 'fld_7FW3A4DF';

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
