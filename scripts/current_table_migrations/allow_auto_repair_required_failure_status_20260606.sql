BEGIN;

ALTER TABLE trading_manager.failure_register
  DROP CONSTRAINT IF EXISTS failure_register_failure_status_check;

ALTER TABLE trading_manager.failure_register
  ADD CONSTRAINT failure_register_failure_status_check
  CHECK (
    failure_status = ANY (
      ARRAY[
        'observed'::text,
        'auto_repair_required'::text,
        'agent_review_required'::text,
        'retry_required'::text,
        'corrected'::text,
        'accepted_skip'::text,
        'unresolved'::text
      ]
    )
  );

COMMIT;
