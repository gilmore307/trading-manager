-- Register pending-only live-call packet planning and terminal-coverage execution guard.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'trm_LCAP006',
    'term',
    'PENDING_ONLY_LIVE_CALL_PACKET_PLANNING',
    'text',
    'pending_only_live_call_packet_planning_v1',
    'trading-manager/docs/95_task_system.md',
    'manager_live_call_approval_proposal_v1;manager_live_call_approval_packet_v1;manager_stage_coverage_v1;trading_manager.failure_register',
    'sync_artifact',
    'Live-call approval planning mode that uses stage coverage to exclude already ready requests and reviewed terminal accepted skips/failures before creating a proposal or packet. It blocks new planning when unreviewed failed requests are present.'
  ),
  (
    'trm_LCAP007',
    'term',
    'TERMINAL_COVERAGE_PROVIDER_EXECUTION_GUARD',
    'text',
    'terminal_coverage_provider_execution_guard_v1',
    'trading-manager/docs/95_task_system.md',
    'manager_provider_dispatch_summary_v1;manager_stage_coverage_v1;live_call_approval_v1',
    'sync_artifact',
    'Provider execution guard used by packet execute command templates. When enabled, execution refuses request ids already ready or reviewed-terminal in stage coverage and refuses to continue while unreviewed failed stage requests exist.'
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
