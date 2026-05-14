-- Register three-lane month-ingest runtime topology and Current Status throughput card.

UPDATE trading_registry
SET payload = '3',
    path = 'trading-manager/deploy/systemd/trading-manager-historical-scheduler.service;trading-manager/deploy/systemd/trading-manager-historical-scheduler.env;trading-manager/src/trading_manager_tasks/scheduler_daemon.py;trading-manager/docs/81_decision.md;trading-manager/docs/98_automation_scheduler.md;trading-manager/docs/99_historical_scheduler_runtime.md',
    applies_to = 'historical_scheduler;month_ingest_worker;worker_count;three_worker_runtime;fold_cadence',
    note = 'Accepted count of parallel month-ingest worker lanes for the non-overlapping six-month historical runtime. Three month-ingest workers plus one serial model worker complete one six-month fold substrate in two ingest rounds.',
    updated_at = NOW()
WHERE id = 'cfg_RFP001';

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'term_RUNTHR001',
    'term',
    'SCHEDULER_RUNTIME_THROUGHPUT_STATUS',
    'text',
    'scheduler_runtime_throughput',
    'trading-storage/src/trading_storage/dashboard_system_status.py;trading-dashboard/web/App.tsx;trading-storage/docs/96_dashboard_read_models.md;trading-dashboard/docs/09_dashboard_read_models.md',
    'current_system_status_summary;runtime_throughput;historical_scheduler;dashboard_current_status',
    'sync_artifact',
    'Sanitized Current Status object summarizing historical scheduler runtime topology and observed decision-log throughput. It replaces provider-thread settings as the primary Multitask/Runtime presentation.'
  ),
  (
    'cfg_RUNTHR001',
    'config',
    'HISTORICAL_RUNTIME_THREE_PLUS_ONE_WORKER_TOPOLOGY',
    'text',
    'month_ingest_workers=3;model_workers=1;fold_months=6;month_ingest_rounds_per_fold=2',
    'trading-manager/docs/81_decision.md;trading-manager/docs/98_automation_scheduler.md;trading-manager/docs/99_historical_scheduler_runtime.md',
    'historical_scheduler;worker_topology;month_ingest_worker;model_worker;fold_cadence',
    'sync_artifact',
    'Accepted historical runtime topology: three month-scoped ingest workers and one serial fold-scoped model worker. Two ingest rounds cover one six-month fold substrate.'
  ),
  (
    'fld_RUNTHR001',
    'field',
    'SCHEDULER_RUNTIME_THROUGHPUT_COMPLETION_RATE_PER_MINUTE',
    'field_name',
    'completion_rate_per_minute',
    'trading-storage/src/trading_storage/dashboard_system_status.py;trading-dashboard/web/App.tsx',
    'current_system_status_summary;runtime_throughput;completion_rate',
    'sync_artifact',
    'Observed executed scheduler decisions per minute over the latest runtime decision-log window.'
  ),
  (
    'fld_RUNTHR002',
    'field',
    'SCHEDULER_RUNTIME_THROUGHPUT_MAX_COMPLETIONS_PER_SECOND',
    'field_name',
    'max_completions_per_second',
    'trading-storage/src/trading_storage/dashboard_system_status.py;trading-dashboard/web/App.tsx',
    'current_system_status_summary;runtime_throughput;burst_rate',
    'sync_artifact',
    'Peak executed scheduler decisions observed in any one-second bucket inside the latest runtime decision-log window.'
  ),
  (
    'fld_RUNTHR003',
    'field',
    'SCHEDULER_RUNTIME_THROUGHPUT_IDLE_OR_BLOCKED_DECISION_COUNT',
    'field_name',
    'idle_or_blocked_decision_count',
    'trading-storage/src/trading_storage/dashboard_system_status.py;trading-dashboard/web/App.tsx',
    'current_system_status_summary;runtime_throughput;idle_blocked_decisions',
    'sync_artifact',
    'Observed scheduler decisions in the throughput window that were not executed or ready, used to show idle/backoff/blocking posture.'
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
