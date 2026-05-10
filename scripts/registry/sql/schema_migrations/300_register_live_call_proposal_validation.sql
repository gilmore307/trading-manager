-- Register exact proposal-bound live-call approval validation.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'trm_LCAP002',
    'term',
    'LIVE_CALL_APPROVAL_PROPOSAL_VALIDATION',
    'text',
    'manager_live_call_approval_proposal_validation_v1',
    'trading-manager/docs/95_task_system.md',
    'manager_live_call_approval_proposal_v1;live_call_approval_v1;provider_dispatch;failure_register;approval_gate',
    'sync_artifact',
    'Plan-only validation proving a reviewed live_call_approval_v1 exactly matches the proposal request ids, excludes registered skips, and passes live-call gate checks before provider dispatch.'
  ),
  (
    'scr_LCAP002',
    'script',
    'MANAGER_VALIDATE_LIVE_CALL_APPROVAL_PROPOSAL',
    'command',
    'PYTHONPATH=src python3 scripts/tasks/validate_live_call_approval_proposal.py',
    '/root/projects/trading-manager/scripts/tasks/validate_live_call_approval_proposal.py',
    'manager_live_call_approval_proposal_validation_v1;manager_live_call_approval_proposal_v1;live_call_approval_v1;approval_gate',
    'sync_artifact',
    'Callable manager entrypoint that validates a reviewed live-call approval exactly against a manager proposal without dispatching providers, activating models, or mutating broker/storage lifecycle state.'
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
