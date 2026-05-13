-- Register the sanitized task timeline now exposed by historical_task_progress_summary.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'cfg_DASHRM011',
    'config',
    'DASHBOARD_HISTORICAL_TASK_TIMELINE',
    'text',
    'historical_task_progress_summary.chart_payload.task_timeline',
    '/root/projects/trading-manager/src/trading_manager_tasks/dashboard_read_models.py',
    'historical_task_progress_summary;dashboard_read_model;task_timeline;past_current_future_tasks;operational_stage_progress',
    'sync_artifact',
    'Manager-owned sanitized task timeline for dashboard Tasks. Lists past/current/future historical workflow stages with phase labels such as data acquisition, feature generation, model generation, model evaluation, promotion review preparation, and maintenance without exposing raw workflow internals.'
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
SET payload = 'web/App.tsx renders historical_task_progress_summary as a list-first Tasks page plus model-specific progress cards under Models',
    applies_to = 'trading-dashboard;tasks;models;historical_modeling;historical_task_progress_summary;task_timeline;read_only_ui',
    note = 'Dashboard Tasks renders a task list from task_timeline; model-specific current-month/current-stage/progress/coverage cards are shown under Models. The UI remains read-only and consumes storage-hosted summaries.',
    updated_at = NOW()
WHERE id = 'cfg_DASHRM008';
