-- Require agent analysis before accepting failed stage coverage requests.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'cfg_MGRFAILREV001',
    'config',
    'MANAGER_FAILED_REQUEST_AGENT_REVIEW_REQUIRED_POLICY',
    'text',
    'all_failed_requests_require_agent_failure_review;accepted_failure_requires_agent_review_ref;preserve_failed_task_state;operator_approval_may_accept_agent_review;do_not_unlock_from_unreviewed_failures',
    'trading-manager/docs/95_task_system.md',
    'manager_stage_coverage_v1;manager_stage_coverage_accepted_failure_review_v1;trading_manager.task_summary',
    'sync_artifact',
    'Every failed component request must be evaluated by an agent before manager can accept the failure as normal/expected and unlock downstream coverage. Accepted-failure coverage requires an agent review evidence reference and preserves failed_count separately from accepted_failed_count.'
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
