-- Require every field entry to declare where the field applies.
-- Target engine: PostgreSQL.

WITH field_usage(key, applies_to) AS (
  VALUES
  ('ACCEPTANCE_OUTCOME', 'acceptance_receipt_slots'),
  ('ACCEPTANCE_REFERENCE', 'execution_key_slots;acceptance_receipt_slots'),
  ('ACCEPTANCE_SUMMARY', 'acceptance_receipt_slots'),
  ('ALLOWED_PATHS', 'execution_key_slots'),
  ('BLOCKED_PATHS', 'execution_key_slots'),
  ('BLOCKED_TASK_LIST', 'maintenance_output_slots'),
  ('CHANGED_FILES', 'completion_receipt_slots'),
  ('CHANGE_SUMMARY', 'completion_receipt_slots'),
  ('CHECK_TIME', 'maintenance_output_slots'),
  ('COMMAND_LIST', 'completion_receipt_slots'),
  ('COMPLETION_RECEIPT_REFERENCE', 'execution_key_slots'),
  ('CONSTRAINTS', 'execution_key_slots'),
  ('DECISION_REFERENCES', 'execution_key_slots;acceptance_receipt_slots'),
  ('DICTIONARY_ISSUE_LIST', 'maintenance_output_slots'),
  ('DOCS_STATUS', 'maintenance_output_slots'),
  ('EXPECTED_OUTPUT', 'execution_key_slots'),
  ('FOLLOW_UP_TASK_LIST', 'maintenance_output_slots'),
  ('ISSUE_LIST', 'completion_receipt_slots;acceptance_receipt_slots'),
  ('MAINTENANCE_STATUS', 'maintenance_output_slots'),
  ('MAINTENANCE_SUMMARY', 'maintenance_output_slots'),
  ('MEMORY_ROUTE_ISSUE_LIST', 'maintenance_output_slots'),
  ('NEXT_TASK_REFERENCE', 'acceptance_receipt_slots'),
  ('OUTPUT_REFERENCE', 'execution_key_slots;completion_receipt_slots'),
  ('PENDING_ACCEPTANCE_LIST', 'maintenance_output_slots'),
  ('PENDING_DISPATCH_LIST', 'maintenance_output_slots'),
  ('REGISTRY_ITEM_APPLIES_TO', 'trading_registry'),
  ('REGISTRY_ITEM_CREATED_AT', 'trading_registry'),
  ('REGISTRY_ITEM_ID', 'trading_registry'),
  ('REGISTRY_ITEM_KEY', 'trading_registry'),
  ('REGISTRY_ITEM_KIND', 'trading_registry'),
  ('REGISTRY_ITEM_NOTE', 'trading_registry'),
  ('REGISTRY_ITEM_PATH', 'trading_registry'),
  ('REGISTRY_ITEM_PAYLOAD', 'trading_registry'),
  ('REGISTRY_ITEM_PAYLOAD_FORMAT', 'trading_registry'),
  ('REGISTRY_ITEM_UPDATED_AT', 'trading_registry'),
  ('REPOSITORY_PATH', 'execution_key_slots;maintenance_output_slots'),
  ('REVIEWED_COMMANDS', 'acceptance_receipt_slots'),
  ('REVIEWED_FILES', 'acceptance_receipt_slots'),
  ('REVIEW_READINESS', 'completion_receipt_slots'),
  ('SPLIT_ISSUE_LIST', 'maintenance_output_slots'),
  ('TASK_GOAL', 'execution_key_slots'),
  ('TASK_IDENTITY', 'task_register_slots;execution_key_slots;completion_receipt_slots;acceptance_receipt_slots'),
  ('TASK_LIFECYCLE_STATE', 'task_register_slots;completion_receipt_slots'),
  ('TASK_SCOPE', 'execution_key_slots'),
  ('TASK_STATUS_SUMMARY', 'maintenance_output_slots'),
  ('TEMPORARY_NEW_NAMES', 'completion_receipt_slots'),
  ('TEST_COMMANDS', 'execution_key_slots'),
  ('TEST_EXPECTATION', 'execution_key_slots'),
  ('TEST_OUTPUT', 'completion_receipt_slots;acceptance_receipt_slots'),
  ('TEST_STATUS', 'completion_receipt_slots;acceptance_receipt_slots'),
  ('WORKFLOW_IDENTITY', 'execution_key_slots;completion_receipt_slots;acceptance_receipt_slots')
)
UPDATE trading_registry target
SET applies_to = field_usage.applies_to
FROM field_usage
WHERE target.kind = 'field'
  AND target.key = field_usage.key;

DO $$
BEGIN
  IF EXISTS (
    SELECT 1
    FROM trading_registry
    WHERE kind = 'field'
      AND (applies_to IS NULL OR BTRIM(applies_to) = '')
  ) THEN
    RAISE EXCEPTION 'all field registry entries must have applies_to';
  END IF;
END;
$$;

ALTER TABLE trading_registry
DROP CONSTRAINT IF EXISTS trading_registry_field_applies_to_check;

ALTER TABLE trading_registry
ADD CONSTRAINT trading_registry_field_applies_to_check
CHECK (kind <> 'field' OR (applies_to IS NOT NULL AND BTRIM(applies_to) <> ''));
