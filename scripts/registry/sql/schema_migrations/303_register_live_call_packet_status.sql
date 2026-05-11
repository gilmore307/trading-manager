-- Register live-call approval packet lifecycle/status closure.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'trm_LCAP004',
    'term',
    'LIVE_CALL_APPROVAL_PACKET_STATUS',
    'text',
    'manager_live_call_approval_packet_status_v1',
    'trading-manager/docs/95_task_system.md',
    'manager_live_call_approval_packet_v1;manager_live_call_approval_proposal_v1;live_call_approval_v1;manager_live_call_approval_proposal_validation_v1;manager_provider_dispatch_summary_v1;manager_provider_stage_reconcile_v1',
    'sync_artifact',
    'Read-only local lifecycle view for a live-call approval packet. It reports template_pending_review, approval_ready_pending_validation, approval_validated_pending_dispatch_plan, dispatch_plan_ready_pending_execute, executed_pending_reconcile, reconciled, or packet_inconsistent without approving, dispatching, or calling providers.'
  ),
  (
    'scr_LCAP004',
    'script',
    'MANAGER_INSPECT_LIVE_CALL_APPROVAL_PACKET',
    'command',
    'PYTHONPATH=src python3 scripts/tasks/inspect_live_call_approval_packet.py',
    '/root/projects/trading-manager/scripts/tasks/inspect_live_call_approval_packet.py',
    'manager_live_call_approval_packet_status_v1;approval_packet;provider_dispatch;stage_reconcile',
    'sync_artifact',
    'Callable manager entrypoint that inspects packet lifecycle status and can write packet_status.json without approving, dispatching, or calling providers.'
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
