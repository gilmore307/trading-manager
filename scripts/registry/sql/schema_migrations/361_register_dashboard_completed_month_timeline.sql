-- Clarify dashboard task timeline coverage across completed historical months.

UPDATE trading_registry
SET applies_to = 'historical_task_progress_summary;dashboard_read_model;task_timeline;completed_month_groups;active_month_group;past_current_future_tasks;operational_stage_progress;expandable_task_detail',
    note = 'Manager-owned sanitized task timeline for dashboard Tasks. Lists completed historical month workflow states plus the active month, with past/current/future operational stage rows and compact expandable detail without exposing raw workflow internals.',
    updated_at = NOW()
WHERE id = 'cfg_DASHRM011';

UPDATE trading_registry
SET applies_to = 'historical_task_progress_summary;dashboard_read_model;task_timeline;completed_month_groups;month_grouping;expandable_task_detail;current_task_progress',
    note = 'Manager-owned sanitized fields for grouping task timeline rows by historical month and expanding a row to show blockers, receipt counts/refs, safety posture, latest execution summary, and matching active-month stage-coverage progress when available. Completed historical months are sourced from durable month workflow-state files.',
    updated_at = NOW()
WHERE id = 'cfg_DASHRM012';
