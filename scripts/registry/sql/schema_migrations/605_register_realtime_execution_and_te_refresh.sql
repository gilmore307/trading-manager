-- Register realtime execution readiness and Trading Economics refresh surfaces.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'art_EXECREAL001',
    'artifact_type',
    'EXECUTION_REALTIME_TRADING_RUNTIME_STATUS',
    'text',
    'execution_realtime_trading_runtime_status',
    'trading-execution/src/trading_execution/runtime/orchestrator.py;trading-execution/docs/40_runtime_model_lifecycle.md',
    'trading-execution;realtime_trading_runtime;active_model_pointer;order_intent_gate;broker_submit_closed',
    'sync_artifact',
    'Execution-owned realtime trading runtime readiness record. It reports waiting-for-promoted-model, active-pointer validation, model activation/order-intent gates, and broker-submit closure without provider calls, model calls, broker calls, order submission, or account mutation.'
  ),
  (
    'scr_EXECREAL001',
    'script',
    'RUN_EXECUTION_REALTIME_TRADING_RUNTIME_CHECK',
    'text',
    'PYTHONPATH=src python3 scripts/execution/run_realtime_trading_runtime_check.py',
    'trading-execution/scripts/execution/run_realtime_trading_runtime_check.py',
    'trading-execution;realtime_trading_runtime;status_check;active_model_pointer',
    'sync_artifact',
    'Callable execution entrypoint that builds the realtime trading runtime readiness status. It can run before a promoted model exists and performs no provider, model, broker, order-submit, or account mutation work.'
  ),
  (
    'scr_DATATE001',
    'script',
    'RUN_TRADING_ECONOMICS_RECENT_CALENDAR_REFRESH',
    'text',
    'PYTHONPATH=src python3 scripts/data/run_trading_economics_recent_calendar_refresh.py',
    'trading-data/scripts/data/run_trading_economics_recent_calendar_refresh.py;trading-data/deploy/systemd/trading-data-te-calendar-refresh.service;trading-data/deploy/systemd/trading-data-te-calendar-refresh.timer',
    'trading-data;trading-economics;calendar_web;recent_refresh;realtime_provider_maintenance;source_data_reuse',
    'sync_artifact',
    'Callable data entrypoint for bounded Trading Economics recent calendar refresh. Plan mode performs no provider call; --execute-live-fetch runs one visible-page recent calendar request under provider-policy controls and writes reusable source rows to storage/01_source_data/realtime.'
  ),
  (
    'cfg_DATATE001',
    'config',
    'TRADING_ECONOMICS_RECENT_CALENDAR_REFRESH_TIMER',
    'text',
    'trading-data-te-calendar-refresh.timer;OnUnitActiveSec=1h;trailing_days=7;forward_days=35',
    'trading-data/deploy/systemd/trading-data-te-calendar-refresh.timer',
    'trading-data;systemd;trading-economics;recent_calendar_refresh;storage_01_source_data',
    'sync_artifact',
    'Systemd timer template for continuously refreshing reusable Trading Economics recent calendar source rows. The service uses the reviewed visible-page route with recent-mode, no authenticated cookies, and provider controls for realtime maintenance.'
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
