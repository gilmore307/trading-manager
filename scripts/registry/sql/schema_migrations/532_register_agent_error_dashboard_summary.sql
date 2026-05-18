-- Register dashboard exposure of agent-error repair status.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'cfg_DASHRM014',
    'config',
    'DASHBOARD_AGENT_ERROR_SUMMARY',
    'text',
    'historical_task_progress_summary.chart_payload.agent_error_summary',
    '/root/projects/trading-manager/src/trading_manager_tasks/dashboard_read_models.py;/root/projects/trading-dashboard/web/App.tsx;/root/projects/trading-dashboard/web/types.ts',
    'historical_task_progress_summary;dashboard_read_model;server_wide_agent_error_handoff;agent_error_summary;owner_facing_error_status',
    'sync_artifact',
    'Manager-owned sanitized agent-error summary for dashboard Diagnostics. It preserves permanent ERR-* refs and exposes diagnosis_status, repair_status, handling_status, retry recommendation, and bounded root-cause text without requiring the dashboard to parse raw agent artifacts.'
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

UPDATE trading_registry
SET note = 'Owner-facing historical modeling task progress summary over active month/window, layer/stage, ready/pending/failed counts, blockers, next system action, and sanitized agent-error repair status with permanent ERR-* refs.',
    updated_at = NOW()
WHERE key = 'HISTORICAL_TASK_PROGRESS_SUMMARY';
