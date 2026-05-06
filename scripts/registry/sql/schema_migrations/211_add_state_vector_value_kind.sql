-- Add a dedicated registry kind for reviewed values inside model state-vector contracts.
-- Keep durable ids stable; this migration only clarifies kind ownership for
-- TargetStateVector V1 block/group/score/window/enum payload tokens.

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
  'data_derived',
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

UPDATE trading_registry
SET kind = 'state_vector_value',
    updated_at = CURRENT_TIMESTAMP
WHERE id IN (
  'fld_TSV007', 'fld_TSV008', 'fld_TSV009', 'fld_TSV010',
  'fld_TSV011', 'fld_TSV012', 'fld_TSV013',
  'fld_TSV015', 'fld_TSV016', 'fld_TSV017', 'fld_TSV018',
  'fld_TSV019', 'fld_TSV020', 'fld_TSV021', 'fld_TSV022',
  'fld_TSV023', 'fld_TSV024', 'fld_TSV025', 'fld_TSV026',
  'fld_TSV027', 'fld_TSV028', 'fld_TSV029', 'fld_TSV030',
  'fld_TSV031', 'fld_TSV032', 'fld_TSV033', 'fld_TSV034',
  'fld_TSV035', 'fld_TSV036', 'fld_TSV037', 'fld_TSV038',
  'fld_TSV039', 'fld_TSV040', 'fld_TSV041', 'fld_TSV042',
  'fld_TSV043', 'fld_TSV044', 'fld_TSV045', 'fld_TSV046',
  'fld_TSV047', 'fld_TSV048', 'fld_TSV049', 'fld_TSV050',
  'fld_TSV051', 'fld_TSV052', 'fld_TSV053', 'fld_TSV054',
  'fld_TSV055', 'fld_TSV056', 'fld_TSV057', 'fld_TSV058',
  'fld_TSV059',
  'trm_TSVWIN001', 'trm_TSVWIN002', 'trm_TSVWIN003', 'trm_TSVWIN004',
  'trm_TSVSC001', 'trm_TSVSC002', 'trm_TSVSC003',
  'trm_TSVWP001'
);
