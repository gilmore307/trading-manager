-- Remove registry rows for project-development slot scopes that do not have
-- accepted current contract files. These draft slot templates were moved out of
-- the OpenClaw skill for review, but their registry rows are intentionally
-- removed until each contract is redesigned and accepted one by one.

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
    'acceptance_receipt_slots',
    'completion_receipt_slots',
    'execution_key_slots',
    'maintenance_output_slots',
    'task_register_slots'
  )
);

DELETE FROM trading_registry
WHERE kind = 'status_value'
AND EXISTS (
  SELECT 1
  FROM regexp_split_to_table(COALESCE(applies_to, ''), ';') AS domain
  WHERE domain IN (
    'acceptance_status',
    'docs_status',
    'maintenance_status',
    'review_status',
    'task_lifecycle_status',
    'test_status'
  )
);
