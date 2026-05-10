-- Register stage coverage accepted-failure exception policy.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'cfg_MGRSTCOV002',
    'config',
    'MANAGER_STAGE_COVERAGE_ACCEPTED_FAILURE_POLICY',
    'text',
    'preserve_failed_count;accepted_failed_count_is_separate;ready_plus_accepted_failed_may_unlock_when_expected_count_met;accepted_failure_requires_review_evidence;do_not_rewrite_failed_tasks_to_ready',
    'trading-manager/docs/95_task_system.md',
    'manager_stage_coverage_v1;manager_model_training_workflow_state_v1;trading_manager.task_summary',
    'sync_artifact',
    'Stage coverage may pass with failed component tasks only when each failure has reviewed accepted-failure evidence, such as not-yet-listed historical absence. The failed task state remains visible; accepted_failed_count is a separate coverage exception count.'
  )
ON CONFLICT (id) DO UPDATE
SET kind = EXCLUDED.kind,
    key = EXCLUDED.key,
    payload_format = EXCLUDED.payload_format,
    payload = EXCLUDED.payload,
    path = EXCLUDED.path,
    applies_to = EXCLUDED.applies_to,
    artifact_sync_policy = EXCLUDED.artifact_sync_policy,
    note = EXCLUDED.note,
    updated_at = NOW();
