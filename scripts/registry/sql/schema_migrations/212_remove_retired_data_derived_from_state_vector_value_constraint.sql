-- Keep the active kind constraint aligned with the retired data_derived boundary
-- while preserving the new state_vector_value kind.

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
  'provider',
  'data_feed',
  'data_source',
  'data_feature',
  'feed_capability',
  'data_kind',
  'template',
  'shared_artifact',
  'script',
  'payload_format',
  'status_value',
  'state_vector_value',
  'artifact_type',
  'manifest_type',
  'ready_signal_type',
  'request_type'
));
