-- Register single-entry manager stage run dashboard/receipt.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'trm_SRDB001',
    'term',
    'MANAGER_STAGE_RUN_DASHBOARD',
    'text',
    'manager_stage_run_dashboard_v1',
    'trading-manager/docs/95_task_system.md',
    'manager_stage_coverage_v1;manager_live_call_approval_packet_status_v1;manager_live_call_approval_packet_v1;manager_provider_dispatch_summary_v1;manager_provider_stage_reconcile_v1;trading_manager.failure_register',
    'sync_artifact',
    'Single human-facing dashboard/receipt for one manager provider-stage/month. It summarizes coverage, packet statuses, next pending-only packet preview, next safe action, and evidence refs while preserving lower-level artifacts as audit attachments.'
  ),
  (
    'scr_SRDB001',
    'script',
    'MANAGER_SUMMARIZE_STAGE_RUN',
    'command',
    'PYTHONPATH=src python3 scripts/tasks/summarize_stage_run.py',
    '/root/projects/trading-manager/scripts/tasks/summarize_stage_run.py',
    'manager_stage_run_dashboard_v1;stage_coverage;approval_packet;provider_dispatch;stage_reconcile',
    'sync_artifact',
    'Callable manager entrypoint that writes or prints the single stage-run dashboard/receipt without dispatching providers or mutating broker/model/storage lifecycle state.'
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
