-- Split request/task parameter collection fields from ordinary/text fields.

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
  'parameter_field',
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
SET kind = 'parameter_field',
    note = 'bundle-specific task parameter object consumed by the data source pipeline. Parameter value carries request/task knobs rather than ordinary output data.'
WHERE id = 'fld_E7E3JEKV';

UPDATE trading_registry
SET kind = 'parameter_field',
    note = 'required and important optional request-parameter collection for the final saved data kind in a source-specific template README. Parameter value carries request/task knobs rather than narrative prose.'
WHERE id = 'fld_EKIND009';
