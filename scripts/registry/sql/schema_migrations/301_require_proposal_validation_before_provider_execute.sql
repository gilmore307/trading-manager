-- Register hard requirement for proposal-bound approval validation before executing provider calls.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'cfg_PDISP002',
    'config',
    'PROVIDER_DISPATCH_EXECUTE_REQUIRES_PROPOSAL_VALIDATION',
    'text',
    'execute_approved_provider_calls requires manager_live_call_approval_proposal_validation_v1 for the exact executable request ids',
    'trading-manager/src/trading_manager_tasks/provider_dispatch.py',
    'manager_provider_dispatch_summary_v1;manager_live_call_approval_proposal_validation_v1;live_call_approval_v1;provider_dispatch',
    'sync_artifact',
    'Provider dispatch may validate approval in plan-only mode, but actual provider execution requires a proposal-bound validation artifact whose approval_id, stage_id, request_ids, gate_validation_count, and plan-only safety flags match the executable live requests.'
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
