-- Split identity/name/locator fields out of ordinary fields and tighten
-- remaining classification axes.

ALTER TABLE trading_registry DROP CONSTRAINT IF EXISTS trading_registry_kind_check;
ALTER TABLE trading_registry
ADD CONSTRAINT trading_registry_kind_check
CHECK (kind IN (
  'field',
  'identity_field',
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
SET kind = 'identity_field',
    note = note || ' Identity value identifies, names, labels, locates, or references an entity/artifact rather than measuring it.'
WHERE id IN (
  'fld_J6FURQOE',
  'fld_H6WM9AVU',
  'fld_FJF5ZAJ5',
  'fld_PS5T5LFZ',
  'fld_F3FORVEW',
  'fld_ETFH009',
  'fld_ETFH005',
  'fld_ETFH010',
  'fld_ETFH004',
  'fld_ETFH001',
  'fld_EVT021',
  'fld_EVT039',
  'fld_EVT010',
  'fld_EVT033',
  'fld_EVT035',
  'fld_EVT034',
  'fld_EVT011',
  'fld_EVT017',
  'fld_MEU005',
  'fld_GDLT001',
  'fld_GDLT003',
  'fld_A7K3P2Q9',
  'fld_ETFH002',
  'fld_BJGL5P8K',
  'fld_OPD003',
  'fld_OPD014',
  'fld_OPD046',
  'fld_OPD045',
  'fld_Z7TPA496',
  'fld_M7Q2P8TZ',
  'fld_4YALJN0B',
  'fld_EKIND002',
  'fld_ABN008',
  'fld_EVT018',
  'fld_STKEX010',
  'fld_MKT001',
  'fld_7X5H7N6Y',
  'fld_EVT001',
  'fld_EVT019',
  'fld_EVT007',
  'fld_ZGTS8P3D'
);

UPDATE trading_registry
SET key = 'OPTION_RIGHT_TYPE',
    payload = 'option_right_type',
    note = 'option contract right/type such as CALL or PUT. Classification value should use a stable lowercase token vocabulary unless the source contract explicitly requires another reviewed encoding.'
WHERE id = 'fld_OPT003';
