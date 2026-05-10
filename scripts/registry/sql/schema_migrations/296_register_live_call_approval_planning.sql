-- Register skip-aware live-call approval proposal planning.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'trm_LCAP001',
    'term',
    'LIVE_CALL_APPROVAL_PROPOSAL',
    'text',
    'manager_live_call_approval_proposal_v1',
    'trading-manager/docs/95_task_system.md',
    'live_call_approval_v1;provider_dispatch;manager_failure_register_v1;manager_request_v1',
    'sync_artifact',
    'Manager-owned review packet that selects exact request ids for a future live_call_approval_v1, excludes registered accepted skips, and remains non-dispatching with provider_calls=0.'
  ),
  (
    'scr_LCAP001',
    'script',
    'MANAGER_PLAN_LIVE_CALL_APPROVAL',
    'command',
    'PYTHONPATH=src python3 scripts/tasks/plan_live_call_approval.py',
    '/root/projects/trading-manager/scripts/tasks/plan_live_call_approval.py',
    'manager_live_call_approval_proposal_v1;live_call_approval_v1;provider_dispatch;failure_register;approval_gate',
    'sync_artifact',
    'Callable manager entrypoint that creates a skip-aware live-call approval review template without approving, dispatching, or calling providers. Review placeholders must be replaced before validation can pass.'
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
