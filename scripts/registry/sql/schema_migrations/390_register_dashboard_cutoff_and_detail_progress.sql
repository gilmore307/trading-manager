-- Register dashboard task-detail presentation and completed-month visibility guard.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'cfg_DASHRM012',
    'config',
    'DASHBOARD_HISTORICAL_TASK_TIMELINE_DETAIL_FIELDS',
    'text',
    'historical_task_progress_summary.chart_payload.task_timeline[].month;historical_task_progress_summary.chart_payload.task_timeline[].detail',
    '/root/projects/trading-manager/src/trading_manager_tasks/dashboard_read_models.py',
    'historical_task_progress_summary;dashboard_read_model;task_timeline;completed_month_groups;month_grouping;expandable_task_detail;current_task_progress',
    'sync_artifact',
    'Manager-owned sanitized fields for grouping task timeline rows by historical month and expanding a row to show blockers, receipt counts/refs, latest execution summary, and matching active-month stage-coverage progress when available. Completed historical months are sourced from durable month workflow-state files.'
  ),
  (
    'cfg_DASHRM013',
    'config',
    'DASHBOARD_TASK_COMPLETED_MONTH_VISIBILITY_GUARD',
    'text',
    'dashboard_task_timeline_excludes_months_after_completed_historical_month_cutoff',
    '/root/projects/trading-manager/src/trading_manager_tasks/dashboard_read_models.py;/root/projects/trading-manager/src/trading_manager_tasks/scheduler_daemon.py',
    'historical_task_progress_summary;dashboard_read_model;task_timeline;completed_month_cutoff;current_month_guard',
    'sync_artifact',
    'Dashboard task timelines apply the completed historical month cutoff in addition to scheduler worker selection, so stale daemon state or pre-created workflow files cannot expose the current incomplete calendar month as a Ready task.'
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
SET path = 'trading-manager/src/trading_manager_tasks/scheduler_daemon.py;trading-manager/src/trading_manager_tasks/dashboard_read_models.py;trading-manager/docs/81_decision.md;trading-manager/docs/99_historical_scheduler_runtime.md',
    applies_to = 'historical_scheduler;provider_downloads;month_ingest_worker;dashboard_task_timeline;current_month_guard',
    note = 'Historical provider downloads and dashboard task timelines are capped at the latest completed calendar month in the project/operator timezone. The current in-progress month is neither downloaded nor exposed as a Ready dashboard task until the next month begins.',
    updated_at = NOW()
WHERE id = 'cfg_HISTCUT001';

UPDATE trading_registry
SET path = 'trading-manager/src/trading_manager_tasks/scheduler_daemon.py;trading-manager/src/trading_manager_tasks/dashboard_read_models.py;trading-manager/docs/81_decision.md',
    applies_to = 'historical_scheduler;month_selection;provider_download_guard;dashboard_task_visibility_guard',
    note = 'Runtime selector and dashboard read-model boundary that prevents month-ingest workers or dashboard task rows from selecting/exposing the current incomplete month for provider-backed historical work.',
    updated_at = NOW()
WHERE id = 'term_HISTCUT001';
