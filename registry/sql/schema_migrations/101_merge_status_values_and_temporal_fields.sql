-- Merge duplicate status values and split temporal field names into their own kind.
-- Status domains remain in applies_to; temporal fields use ISO-8601 value semantics.

UPDATE trading_registry
SET key = 'STATUS_ACCEPTED',
    applies_to = 'acceptance_outcome;task_lifecycle_state',
    note = 'shared status value for accepted work or lifecycle acceptance states'
WHERE id = 'aco_Q1M7D4LP';

UPDATE trading_registry
SET key = 'STATUS_BLOCKED',
    applies_to = 'acceptance_outcome;docs_status;maintenance_status;review_readiness;task_lifecycle_state',
    note = 'shared status value for blocked work, review, docs, maintenance, or lifecycle states'
WHERE id = 'aco_H7Y4P1ZD';

UPDATE trading_registry
SET key = 'STATUS_REJECTED',
    applies_to = 'acceptance_outcome;task_lifecycle_state',
    note = 'shared status value for rejected work or lifecycle rejection states'
WHERE id = 'aco_B8T3W6FN';

DELETE FROM trading_registry
WHERE id IN (
  'tls_H1V8L4TE',
  'dcs_X9K5F1VC',
  'mns_B5N1K6XD',
  'rrd_V9H5C2KR',
  'tls_K5Q7F2MD',
  'tls_N7B2P5XK'
);

ALTER TABLE trading_registry
DROP CONSTRAINT IF EXISTS trading_registry_kind_check;

UPDATE trading_registry
SET kind = 'temporal_field',
    payload_format = 'field_name',
    note = note || ' Temporal value format: ISO 8601; dates use YYYY-MM-DD and datetimes/times include explicit timezone or ET suffix semantics.'
WHERE kind = 'field'
  AND key IN (
    'AS_OF_DATE',
    'CHECK_TIME',
    'DATA_TASK_RUN_COMPLETED_AT',
    'DATA_TASK_RUN_STARTED_AT',
    'DATA_TIMESTAMP_ET',
    'EVENT_EFFECTIVE_TIME_ET',
    'EVENT_FACTOR_AS_OF_ET',
    'EVENT_TIME_ET',
    'OPTION_EXPIRATION',
    'REGISTRY_ITEM_CREATED_AT',
    'REGISTRY_ITEM_UPDATED_AT',
    'SNAPSHOT_TIME_ET',
    'STOCK_ETF_AVAILABLE_TIME_ET',
    'TIMELINE_CREATED_AT_ET',
    'TIMELINE_UPDATED_AT_ET',
    'TRADE_TIMESTAMP_ET',
    'UNDERLYING_TIMESTAMP_ET',
    'WINDOW_END_ET',
    'WINDOW_START_ET'
  );

ALTER TABLE trading_registry
ADD CONSTRAINT trading_registry_kind_check
CHECK (kind IN (
  'field',
  'temporal_field',
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
