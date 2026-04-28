-- Tighten classification axes and split path/reference locators from identity fields.

ALTER TABLE trading_registry DROP CONSTRAINT IF EXISTS trading_registry_kind_check;
ALTER TABLE trading_registry
ADD CONSTRAINT trading_registry_kind_check
CHECK (kind IN (
  'field',
  'identity_field',
  'path_field',
  'temporal_field',
  'classification_field',
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
SET key = 'ACCEPTANCE_STATUS',
    payload = 'acceptance_status',
    note = 'canonical shared status field for acceptance receipt slots. Classification value should use a stable lowercase token vocabulary unless the source contract explicitly requires another reviewed encoding.'
WHERE id = 'fld_GI3OL5K5';

UPDATE trading_registry
SET key = 'REVIEW_STATUS',
    payload = 'review_status',
    note = 'canonical shared review status field for completion receipt slots. Classification value should use a stable lowercase token vocabulary unless the source contract explicitly requires another reviewed encoding.'
WHERE id = 'fld_6RJNNWV1';

UPDATE trading_registry
SET key = 'REGISTRY_ITEM_ARTIFACT_SYNC_POLICY_TYPE',
    payload = 'artifact_sync_policy_type',
    note = 'semantic artifact sync policy type field corresponding to trading_registry.artifact_sync_policy. Classification value should use a stable lowercase token vocabulary unless the source contract explicitly requires another reviewed encoding.'
WHERE id = 'fld_R9K2H7AP';

UPDATE trading_registry
SET applies_to = replace(replace(replace(applies_to,
    'acceptance_outcome', 'acceptance_status'),
    'review_readiness', 'review_status'),
    'trading_registry.artifact_sync_policy', 'artifact_sync_policy_type')
WHERE kind = 'status_value';

UPDATE trading_registry
SET key = replace(key, 'ACCEPTANCE_OUTCOME', 'ACCEPTANCE_STATUS'),
    note = replace(note, 'acceptance outcome', 'acceptance status')
WHERE kind = 'status_value' AND key LIKE 'ACCEPTANCE_OUTCOME_%';

UPDATE trading_registry
SET key = replace(key, 'REVIEW_READINESS', 'REVIEW_STATUS'),
    note = replace(note, 'review readiness', 'review status')
WHERE kind = 'status_value' AND key LIKE 'REVIEW_READINESS_%';

UPDATE trading_registry
SET key = replace(key, 'ARTIFACT_SYNC_POLICY', 'ARTIFACT_SYNC_POLICY_TYPE'),
    note = replace(note, 'policy values', 'policy type values')
WHERE kind = 'status_value' AND key LIKE 'ARTIFACT_SYNC_POLICY_%';

UPDATE trading_registry
SET kind = 'path_field',
    note = regexp_replace(note, ' Identity value identifies, names, labels, locates, or references an entity/artifact rather than measuring it\.$', '') || ' Path value locates or references an artifact, file, URL, source reference, output reference, or repository path.'
WHERE id IN (
  'fld_YLTWJKTJ',
  'fld_H2OBUVA0',
  'fld_9BAEN7ZS',
  'fld_EKIND011',
  'fld_PPBXKTON',
  'fld_U3G3BLPO',
  'fld_ES5OZEMA',
  'fld_F4OFEVFJ',
  'fld_Q9KQLPH4',
  'fld_TEC005',
  'fld_J6FURQOE',
  'fld_H6WM9AVU',
  'fld_EVT021',
  'fld_EVT035',
  'fld_EVT034',
  'fld_EVT017',
  'fld_BJGL5P8K',
  'fld_Z7TPA496',
  'fld_M7Q2P8TZ',
  'fld_4YALJN0B',
  'fld_ABN008',
  'fld_EVT018',
  'fld_STKEX010',
  'fld_EVT007'
);

UPDATE trading_registry
SET note = regexp_replace(note, ' Identity value identifies, names, labels, locates, or references an entity/artifact rather than measuring it\.$', '') || ' Identity value identifies or names an entity/artifact rather than measuring or locating it.'
WHERE kind = 'identity_field';
