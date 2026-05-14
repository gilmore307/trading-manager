-- Register dashboard task worker preview fields for owner-facing task rows.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'fld_DASHTASK010',
    'field',
    'DASHBOARD_TASK_WORKER_ID',
    'field_name',
    'worker_id',
    'trading-manager/src/trading_manager_tasks/dashboard_read_models.py;trading-dashboard/web/types.ts;trading-dashboard/web/App.tsx;trading-dashboard/docs/09_dashboard_read_models.md',
    'historical_task_progress_summary;task_timeline;dashboard_tasks;task_worker_preview',
    'sync_artifact',
    'Owner-facing task timeline worker identifier showing which manager/provider/fold worker owns or executes a task preview row.'
  ),
  (
    'fld_DASHTASK011',
    'field',
    'DASHBOARD_TASK_WORKER_LABEL',
    'field_name',
    'worker_label',
    'trading-manager/src/trading_manager_tasks/dashboard_read_models.py;trading-dashboard/web/types.ts;trading-dashboard/web/App.tsx;trading-dashboard/docs/09_dashboard_read_models.md',
    'historical_task_progress_summary;task_timeline;dashboard_tasks;task_worker_preview',
    'sync_artifact',
    'Owner-facing task timeline worker label rendered in each task preview and expandable task detail panel.'
  ),
  (
    'fld_DASHTASK012',
    'field',
    'DASHBOARD_TASK_WORKER_KIND',
    'field_name',
    'worker_kind',
    'trading-manager/src/trading_manager_tasks/dashboard_read_models.py;trading-dashboard/web/types.ts;trading-dashboard/web/App.tsx;trading-dashboard/docs/09_dashboard_read_models.md',
    'historical_task_progress_summary;task_timeline;dashboard_tasks;task_worker_preview',
    'sync_artifact',
    'Owner-facing worker category for dashboard task rows, such as scheduler_stage, provider_pool, or fold_worker.'
  ),
  (
    'fld_DASHTASK013',
    'field',
    'DASHBOARD_PROVIDER_DISPATCH_WORKER_PREVIEW',
    'field_name',
    'worker_preview',
    'trading-manager/src/trading_manager_tasks/stage_run_dashboard.py',
    'manager_stage_run_dashboard;provider_dispatch_preview;task_worker_preview',
    'sync_artifact',
    'Owner-facing provider dispatch preview rows showing request id, worker id, worker slot, and dispatch status before execution.'
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
