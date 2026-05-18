-- Register the realtime Trading Economics due-release retry policy.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES (
  'cfg_TECAL002',
  'config',
  'TE_RECENT_RELEASE_FETCH_RETRY_POLICY',
  'text',
  'te_recent_release_fetch_retry_after_10s_once',
  'trading-manager/docs/20_task_system.md;/root/projects/trading-manager/src/trading_manager_tasks/trading_economics_calendar.py',
  'trading_economics_calendar_web;realtime_recent_calendar;due_release_refresh;release_actual_update;manager_task_system;source_09_event_risk_governor',
  'sync_artifact',
  'Realtime TE release maintenance policy: fetch immediately when a scheduled release becomes due; if the fetch fails, retry once after 10 seconds. Successful fetches with no actual value remain delayed/pending evidence and do not authorize model activation, broker execution, order placement, or account mutation.'
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
