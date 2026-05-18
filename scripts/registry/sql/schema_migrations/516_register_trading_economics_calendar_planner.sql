-- Register the Trading Economics calendar seed/recent maintenance planner.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES (
  'scr_TECALE1',
  'script',
  'TRADING_ECONOMICS_CALENDAR_PLAN',
  'command',
  'PYTHONPATH=src python3 scripts/tasks/plan_trading_economics_calendar.py',
  '/root/projects/trading-manager/scripts/tasks/plan_trading_economics_calendar.py;/root/projects/trading-manager/src/trading_manager_tasks/trading_economics_calendar.py',
  'trading-manager;trading-data;trading_economics_calendar_web;source_09_event_risk_governor;event_risk_governor;historical_seed;realtime_recent_calendar;manager_task_system',
  'sync_artifact',
  'Stable callable planner for Trading Economics calendar maintenance. The historical-seed mode prepares filtered one-artifact-per-month source_09_event_risk_governor task keys from saved TE calendar-web artifacts without provider calls. The recent-poll mode prepares logged-out recent calendar feed task keys with realtime_provider_maintenance controls and no API/download/export route, model activation, broker execution, or account mutation.'
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
