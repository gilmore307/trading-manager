-- Register complete live-call approval packet bundle generation.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'trm_LCAP003',
    'term',
    'LIVE_CALL_APPROVAL_PACKET',
    'text',
    'manager_live_call_approval_packet_v1',
    'trading-manager/docs/95_task_system.md',
    'manager_live_call_approval_proposal_v1;live_call_approval_v1;manager_live_call_approval_proposal_validation_v1;manager_provider_dispatch_summary_v1;manager_provider_stage_reconcile_v1',
    'sync_artifact',
    'Local runtime bundle containing a proposal, reviewed approval placeholder, validation output target, dispatch command templates, and reconcile command template for one exact live-call request set. Packet creation is non-dispatching and provider_calls=0.'
  ),
  (
    'scr_LCAP003',
    'script',
    'MANAGER_CREATE_LIVE_CALL_APPROVAL_PACKET',
    'command',
    'PYTHONPATH=src python3 scripts/tasks/create_live_call_approval_packet.py',
    '/root/projects/trading-manager/scripts/tasks/create_live_call_approval_packet.py',
    'manager_live_call_approval_packet_v1;approval_packet;provider_dispatch;stage_reconcile',
    'sync_artifact',
    'Callable manager entrypoint that writes a complete local approval packet bundle without approving, dispatching, or calling providers.'
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
