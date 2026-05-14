-- Register historical scheduler provider parallelism/status dashboard fields.
-- These are owner-facing read-model fields; active code must treat schema names as source-owned contracts,
-- not infer new business names from registry payload values.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'term_SCHEDPAR001',
    'term',
    'SCHEDULER_PARALLELISM_STATUS',
    'text',
    'scheduler_parallelism_status',
    'trading-manager/docs/81_decision.md;trading-storage/docs/96_dashboard_read_models.md;trading-dashboard/docs/09_dashboard_read_models.md',
    'current_system_status_summary;dashboard_status;historical_scheduler;provider_parallelism',
    'sync_artifact',
    'Sanitized Current Status read-model object describing bounded dynamic provider worker selection and service-configured concurrency parameters.'
  ),
  (
    'fld_SCHEDPAR001',
    'field',
    'SCHEDULER_PARALLELISM_SELECTED_WORKER_COUNT',
    'field_name',
    'selected_worker_count',
    'trading-storage/docs/96_dashboard_read_models.md;trading-dashboard/docs/09_dashboard_read_models.md',
    'current_system_status_summary;parallelism;provider_workers',
    'sync_artifact',
    'Current provider worker thread count selected from request count, load, and memory headroom.'
  ),
  (
    'fld_SCHEDPAR002',
    'field',
    'SCHEDULER_PARALLELISM_MAX_WORKER_COUNT',
    'field_name',
    'max_worker_count',
    'trading-storage/docs/96_dashboard_read_models.md;trading-dashboard/docs/09_dashboard_read_models.md',
    'current_system_status_summary;parallelism;provider_workers',
    'sync_artifact',
    'Configured maximum provider worker threads for one bounded historical acquisition dispatch slice.'
  ),
  (
    'fld_SCHEDPAR003',
    'field',
    'SCHEDULER_PARALLELISM_NEXT_REQUEST_LIMIT',
    'field_name',
    'next_request_limit',
    'trading-storage/docs/96_dashboard_read_models.md;trading-dashboard/docs/09_dashboard_read_models.md',
    'current_system_status_summary;parallelism;provider_batch',
    'sync_artifact',
    'Configured maximum provider requests admitted into one scheduler dispatch tick.'
  ),
  (
    'fld_SCHEDPAR004',
    'field',
    'SCHEDULER_PARALLELISM_SCHEDULER_INTERVAL_SECONDS',
    'field_name',
    'scheduler_interval_seconds',
    'trading-storage/docs/96_dashboard_read_models.md;trading-dashboard/docs/09_dashboard_read_models.md',
    'current_system_status_summary;parallelism;service_tick',
    'sync_artifact',
    'Historical scheduler daemon tick interval visible on the Current Status multitask card.'
  ),
  (
    'fld_SCHEDPAR005',
    'field',
    'SCHEDULER_PARALLELISM_LOAD_TARGET_PER_CPU',
    'field_name',
    'load_target_per_cpu',
    'trading-storage/docs/96_dashboard_read_models.md;trading-dashboard/docs/09_dashboard_read_models.md',
    'current_system_status_summary;parallelism;resource_gate',
    'sync_artifact',
    'Per-CPU load target used to bound dynamic historical provider worker selection.'
  ),
  (
    'fld_SCHEDPAR006',
    'field',
    'SCHEDULER_PARALLELISM_WORKER_MEMORY_MB',
    'field_name',
    'worker_memory_mb',
    'trading-storage/docs/96_dashboard_read_models.md;trading-dashboard/docs/09_dashboard_read_models.md',
    'current_system_status_summary;parallelism;resource_gate',
    'sync_artifact',
    'Estimated memory budget per provider worker used by the dashboard status calculation.'
  ),
  (
    'fld_SCHEDPAR007',
    'field',
    'SCHEDULER_PARALLELISM_RESERVED_MEMORY_MB',
    'field_name',
    'reserved_memory_mb',
    'trading-storage/docs/96_dashboard_read_models.md;trading-dashboard/docs/09_dashboard_read_models.md',
    'current_system_status_summary;parallelism;resource_gate',
    'sync_artifact',
    'Memory reserve kept outside the provider worker dynamic-selection budget.'
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
