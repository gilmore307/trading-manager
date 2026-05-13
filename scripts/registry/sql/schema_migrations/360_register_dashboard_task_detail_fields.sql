-- Register dashboard task timeline month grouping and expandable detail fields.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'cfg_DASHRM012',
    'config',
    'DASHBOARD_HISTORICAL_TASK_TIMELINE_DETAIL_FIELDS',
    'text',
    'historical_task_progress_summary.chart_payload.task_timeline[].month;historical_task_progress_summary.chart_payload.task_timeline[].detail',
    '/root/projects/trading-manager/src/trading_manager_tasks/dashboard_read_models.py',
    'historical_task_progress_summary;dashboard_read_model;task_timeline;month_grouping;expandable_task_detail;current_task_progress',
    'sync_artifact',
    'Manager-owned sanitized fields for grouping task timeline rows by historical month and expanding a row to show blockers, receipt counts/refs, safety posture, latest execution summary, and matching stage-coverage progress when available.'
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
SET applies_to = 'historical_task_progress_summary;dashboard_read_model;task_timeline;month_grouping;past_current_future_tasks;operational_stage_progress;expandable_task_detail',
    note = 'Manager-owned sanitized task timeline for dashboard Tasks. Lists past/current/future historical workflow stages with month grouping, phase labels such as data acquisition and feature generation, and compact expandable detail without exposing raw workflow internals.'
WHERE id = 'cfg_DASHRM011';
