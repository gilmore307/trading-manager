-- Registry rows describe semantic fields, not per-template spelling variants.
-- Merge created_at_et/updated_at_et into canonical created_at/updated_at and
-- split categorical/classification slots into classification_field.

UPDATE trading_registry
SET applies_to = 'trading_registry;event_timeline_template;option_activity_event_detail_template',
    note = 'canonical created-at timestamp field shared by registry rows and event/detail templates. Temporal value format: ISO 8601 with explicit timezone semantics when a datetime is emitted.'
WHERE id = 'fld_P8L2C4TY';

UPDATE trading_registry
SET applies_to = 'trading_registry;event_timeline_template;option_activity_event_detail_template',
    note = 'canonical updated-at timestamp field shared by registry rows and event/detail templates. Temporal value format: ISO 8601 with explicit timezone semantics when a datetime is emitted.'
WHERE id = 'fld_Q5F9M2NZ';

DELETE FROM trading_registry
WHERE id IN ('fld_EVT003', 'fld_EVT004');

ALTER TABLE trading_registry
DROP CONSTRAINT IF EXISTS trading_registry_kind_check;

UPDATE trading_registry
SET kind = 'classification_field',
    payload_format = 'field_name',
    note = note || ' Classification value should use a stable lowercase token vocabulary unless the source contract explicitly requires another reviewed encoding.'
WHERE kind = 'field'
  AND key IN (
    'ABNORMAL_ACTIVITY_TYPE',
    'ACCEPTANCE_OUTCOME',
    'DATA_KIND',
    'DOCS_STATUS',
    'ETF_HOLDING_ASSET_CLASS',
    'ETF_HOLDING_SECTOR',
    'EVENT_ANALYSIS_STATUS',
    'EVENT_DEDUP_STATUS',
    'EVENT_IMPACT_SCOPE',
    'EVENT_TYPE',
    'EXPOSURE_TYPE',
    'GDELT_IMPACT_SCOPE_HINT',
    'GDELT_THEMES',
    'MAINTENANCE_STATUS',
    'OPTION_EVENT_DETAIL_SIDE_HINT',
    'OPTION_RIGHT',
    'REGISTRY_ITEM_ARTIFACT_SYNC_POLICY',
    'REGISTRY_ITEM_KIND',
    'REVIEW_READINESS',
    'SOURCE_TYPE',
    'STATUS',
    'STOCK_ETF_STYLE_TAGS',
    'TASK_LIFECYCLE_STATE',
    'TASK_SCOPE',
    'TEST_STATUS',
    'TRADING_ECONOMICS_CATEGORY',
    'UNIVERSE_TYPE'
  );

ALTER TABLE trading_registry
ADD CONSTRAINT trading_registry_kind_check
CHECK (kind IN (
  'field',
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
