-- Remove unaccepted data-task architecture registry rows. Task key,
-- completion receipt, and data task template contracts will be redesigned after
-- the model/bundle architecture is settled, then re-registered one by one.

DELETE FROM trading_registry
WHERE kind IN (
  'field',
  'identity_field',
  'path_field',
  'temporal_field',
  'classification_field',
  'text_field',
  'parameter_field'
)
AND EXISTS (
  SELECT 1
  FROM regexp_split_to_table(COALESCE(applies_to, ''), ';') AS scope
  WHERE scope IN (
    'data_task_key',
    'data_task_completion_receipt',
    'data_task_completion_receipt_run'
  )
);

DELETE FROM trading_registry
WHERE key IN (
  'DATA_TASK_KEY_TEMPLATE',
  'DATA_TASK_COMPLETION_RECEIPT_TEMPLATE',
  'DATA_SOURCE_BUNDLE_README_TEMPLATE',
  'DATA_SOURCE_FETCH_SPEC_TEMPLATE',
  'DATA_SOURCE_CLEAN_SPEC_TEMPLATE',
  'DATA_SOURCE_SAVE_SPEC_TEMPLATE',
  'DATA_SOURCE_PIPELINE_TEMPLATE',
  'DATA_SOURCE_FIXTURE_POLICY_TEMPLATE',
  'DATA_TASK_KEY_FILE',
  'DATA_TASK_COMPLETION_RECEIPT',
  'DATA_TASK_RUN',
  'TRADING_DATA_DEVELOPMENT_STORAGE_ROOT'
);
