-- Register the historical-download completed-month cutoff policy.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'cfg_HISTCUT001',
    'config',
    'HISTORICAL_DOWNLOAD_COMPLETED_MONTH_CUTOFF',
    'text',
    'latest_completed_calendar_month_in_America_New_York',
    'trading-manager/src/trading_manager_tasks/scheduler_daemon.py;trading-manager/docs/81_decision.md;trading-manager/docs/99_historical_scheduler_runtime.md',
    'historical_scheduler;provider_downloads;month_ingest_worker;current_month_guard',
    'sync_artifact',
    'Historical provider downloads are capped at the latest completed calendar month in the project/operator timezone. The current in-progress month is not downloaded until the next month begins.'
  ),
  (
    'term_HISTCUT001',
    'term',
    'COMPLETED_HISTORICAL_MONTH_CUTOFF',
    'text',
    'completed_historical_month_cutoff',
    'trading-manager/src/trading_manager_tasks/scheduler_daemon.py;trading-manager/docs/81_decision.md',
    'historical_scheduler;month_selection;provider_download_guard',
    'sync_artifact',
    'Runtime selector boundary that prevents month-ingest workers from selecting the current incomplete month for provider downloads.'
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
