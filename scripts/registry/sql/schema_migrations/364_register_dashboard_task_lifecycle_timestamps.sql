-- Register dashboard task timeline lifecycle timestamp fields.
-- These are owner-facing read-model fields, not dashboard access to raw workflow internals.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'fld_DASHTASK006',
    'temporal_field',
    'DASHBOARD_TASK_CREATED_AT',
    'field_name',
    'created_at_utc',
    'trading-manager/docs/81_decision.md;trading-dashboard/docs/09_dashboard_read_models.md',
    'historical_task_progress_summary;task_timeline;dashboard_tasks;task_lifecycle_timestamps',
    'sync_artifact',
    'Owner-facing task timeline timestamp for when the dashboard task/stage row was generated or first available from manager evidence.'
  ),
  (
    'fld_DASHTASK007',
    'temporal_field',
    'DASHBOARD_TASK_STARTED_AT',
    'field_name',
    'started_at_utc',
    'trading-manager/docs/81_decision.md;trading-dashboard/docs/09_dashboard_read_models.md',
    'historical_task_progress_summary;task_timeline;dashboard_tasks;task_lifecycle_timestamps',
    'sync_artifact',
    'Owner-facing task timeline timestamp for when execution started, derived from sanitized workflow or receipt timing metadata when available.'
  ),
  (
    'fld_DASHTASK008',
    'temporal_field',
    'DASHBOARD_TASK_ENDED_AT',
    'field_name',
    'ended_at_utc',
    'trading-manager/docs/81_decision.md;trading-dashboard/docs/09_dashboard_read_models.md',
    'historical_task_progress_summary;task_timeline;dashboard_tasks;task_lifecycle_timestamps',
    'sync_artifact',
    'Owner-facing task timeline timestamp for when execution or terminal status ended, derived from sanitized workflow or receipt timing metadata when available.'
  ),
  (
    'fld_DASHTASK009',
    'temporal_field',
    'DASHBOARD_TASK_STATUS_UPDATED_AT',
    'field_name',
    'status_updated_at_utc',
    'trading-manager/docs/81_decision.md;trading-dashboard/docs/09_dashboard_read_models.md',
    'historical_task_progress_summary;task_timeline;dashboard_tasks;task_lifecycle_timestamps',
    'sync_artifact',
    'Owner-facing task timeline timestamp for the latest status update/recalculation used to judge whether a task is still moving.'
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
