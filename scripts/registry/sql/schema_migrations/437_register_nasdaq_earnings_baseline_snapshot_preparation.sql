-- Register manager preparation for future Nasdaq earnings EPS baseline snapshots.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'scr_NEBP001',
    'script',
    'MANAGER_PREPARE_NASDAQ_EARNINGS_BASELINE_SNAPSHOTS',
    'text',
    'PYTHONPATH=src python3 scripts/tasks/prepare_nasdaq_earnings_baseline_snapshots.py',
    'trading-manager/scripts/tasks/prepare_nasdaq_earnings_baseline_snapshots.py',
    'manager_task_system;nasdaq_earnings_calendar;expectation_baseline;event_risk_governor',
    'sync_artifact',
    'Manager-owned no-provider preparation script for future Nasdaq earnings EPS-consensus baseline snapshot task keys targeting trading-execution calendar_discovery.'
  ),
  (
    'trm_NEBP001',
    'term',
    'NASDAQ_EARNINGS_BASELINE_SNAPSHOT_REQUEST',
    'text',
    'expectation_baseline_snapshot',
    'trading-manager/src/trading_manager_tasks/nasdaq_earnings_baseline.py',
    'manager_task_system;nasdaq_earnings_calendar;expectation_baseline',
    'sync_artifact',
    'Manager request kind for future earnings-calendar baseline snapshots; currently accepted for Nasdaq EPS-consensus candidate capture only.'
  ),
  (
    'cfg_NEBP001',
    'config',
    'NASDAQ_EARNINGS_BASELINE_TASK_KEY_STORAGE_POLICY',
    'text',
    'storage/earnings_guidance_baseline/nasdaq_earnings_calendar/YYYY-MM-DD/task_key.json',
    'trading-manager/docs/95_task_system.md',
    'manager_task_system;expectation_baseline;nasdaq_earnings_calendar',
    'sync_artifact',
    'Prepared Nasdaq baseline snapshot task keys are stored by calendar date under the manager earnings_guidance_baseline namespace.'
  ),
  (
    'cfg_NEBP002',
    'config',
    'NASDAQ_EARNINGS_BASELINE_USE_POLICY',
    'text',
    'use_epsForecast_only_when_captured_before_event;exclude_eps_actual_and_surprise_fields',
    'trading-manager/src/trading_manager_tasks/nasdaq_earnings_baseline.py',
    'nasdaq_earnings_calendar;expectation_baseline;point_in_time_policy;signed_direction_claims',
    'sync_artifact',
    'Future Nasdaq EPS baseline artifacts may use pre-event EPS forecast fields only; actual EPS and surprise fields are forbidden baseline inputs.'
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
