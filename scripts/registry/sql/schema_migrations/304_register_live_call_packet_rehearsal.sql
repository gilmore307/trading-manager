-- Register live-call approval packet plan rehearsal.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'trm_LCAP005',
    'term',
    'LIVE_CALL_APPROVAL_PACKET_REHEARSAL',
    'text',
    'manager_live_call_approval_packet_rehearsal_v1',
    'trading-manager/docs/95_task_system.md',
    'manager_live_call_approval_packet_v1;manager_live_call_approval_packet_status_v1;manager_live_call_approval_proposal_validation_v1;manager_provider_dispatch_summary_v1',
    'sync_artifact',
    'Plan-only rehearsal for a live-call approval packet. It uses ephemeral approval files to validate proposal mechanics and run plan-only dispatch without writing persistent approval/validation/dispatch artifacts, without changing packet status, and with provider_calls=0.'
  ),
  (
    'scr_LCAP005',
    'script',
    'MANAGER_REHEARSE_LIVE_CALL_APPROVAL_PACKET',
    'command',
    'PYTHONPATH=src python3 scripts/tasks/rehearse_live_call_approval_packet.py',
    '/root/projects/trading-manager/scripts/tasks/rehearse_live_call_approval_packet.py',
    'manager_live_call_approval_packet_rehearsal_v1;approval_packet;proposal_validation;provider_dispatch_plan',
    'sync_artifact',
    'Callable manager entrypoint that rehearses packet validation plus plan-only provider dispatch through temporary approval files and never executes provider calls.'
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
