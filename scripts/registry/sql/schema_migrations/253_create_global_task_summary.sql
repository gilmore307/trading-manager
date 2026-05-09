-- Create a global task summary surface sorted by manager priority policy.
-- This is a derived read model over durable control-plane facts, not a second
-- owner of task state.

CREATE OR REPLACE VIEW trading_manager.task_summary AS
WITH request_base AS (
  SELECT
    request_id,
    contract_type,
    request_kind,
    status AS request_status,
    created_at_utc,
    requested_by,
    target_component_id,
    target_component_kind,
    target_repo_id,
    expected_outputs,
    policy_refs,
    COALESCE(NULLIF(LOWER(priority), ''), 'normal') AS priority,
    deadline_at_utc,
    parameter_ref,
    dry_run
  FROM trading_manager.manager_request
), prioritized AS (
  SELECT
    *,
    CASE priority
      WHEN 'critical' THEN 10
      WHEN 'high' THEN 20
      WHEN 'normal' THEN 30
      WHEN 'low' THEN 40
      WHEN 'backlog' THEN 50
      ELSE 30
    END AS priority_rank
  FROM request_base
)
SELECT
  r.request_id,
  r.contract_type,
  r.request_kind,
  COALESCE(latest_signal.status, latest_run.status, r.request_status) AS task_status,
  r.request_status,
  r.priority,
  r.priority_rank,
  r.deadline_at_utc,
  r.created_at_utc,
  r.requested_by,
  r.target_repo_id,
  r.target_component_id,
  r.target_component_kind,
  r.dry_run,
  r.parameter_ref,
  r.expected_outputs,
  r.policy_refs,
  latest_run.run_id AS latest_run_id,
  latest_run.status AS latest_run_status,
  latest_run.started_at_utc AS latest_run_started_at_utc,
  latest_run.ended_at_utc AS latest_run_ended_at_utc,
  latest_run.error_summary AS latest_run_error_summary,
  latest_signal.ready_signal_id AS latest_ready_signal_id,
  latest_signal.status AS latest_ready_signal_status,
  latest_signal.review_required AS latest_ready_signal_review_required,
  latest_signal.blocking_reason AS latest_ready_signal_blocking_reason,
  COALESCE(artifact_counts.artifact_count, 0) AS artifact_count
FROM prioritized r
LEFT JOIN LATERAL (
  SELECT rm.*
  FROM trading_manager.run_manifest rm
  WHERE rm.request_id = r.request_id
  ORDER BY rm.started_at_utc DESC, rm.run_id DESC
  LIMIT 1
) latest_run ON TRUE
LEFT JOIN LATERAL (
  SELECT rs.*
  FROM trading_manager.ready_signal rs
  JOIN trading_manager.run_manifest rm ON rm.run_id = rs.producer_run_id
  WHERE rm.request_id = r.request_id
    AND rs.supersedes_ready_signal_id IS NULL
  ORDER BY rs.created_at_utc DESC, rs.ready_signal_id DESC
  LIMIT 1
) latest_signal ON TRUE
LEFT JOIN LATERAL (
  SELECT COUNT(*)::BIGINT AS artifact_count
  FROM trading_manager.artifact_ref ar
  JOIN trading_manager.run_manifest rm ON rm.run_id = ar.producer_run_id
  WHERE rm.request_id = r.request_id
) artifact_counts ON TRUE;

COMMENT ON VIEW trading_manager.task_summary IS
  'Global manager task summary sorted by priority_rank/deadline/created_at at query time. Derived from manager_request, run_manifest, artifact_ref, and ready_signal; does not own task state.';

UPDATE trading_registry
SET payload = 'trading_manager.manager_request;trading_manager.input_binding;trading_manager.run_manifest;trading_manager.run_step;trading_manager.artifact_ref;trading_manager.ready_signal;trading_manager.task_summary',
    path = 'trading-manager/docs/95_task_system.md',
    applies_to = 'trading-manager;control_plane;task_system;component_requests;component_completion_receipts;global_task_summary',
    note = 'Minimal manager task-system tables plus the derived global task_summary view. Requests are centralized in manager_request; component completion receipts are normalized into run_manifest, artifact_ref, and ready_signal rows; task_summary is read-only derived state.',
    updated_at = NOW()
WHERE key = 'MANAGER_CONTRACT_SQL_TABLES';

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'cfg_MTS003',
    'config',
    'MANAGER_TASK_PRIORITY_VALUES',
    'text',
    'critical;high;normal;low;backlog',
    'trading-manager/docs/95_task_system.md',
    'task_system;manager_request_v1;task_summary;priority_ordering',
    'sync_artifact',
    'Accepted manager task priority values in descending order. Default priority is normal.'
  ),
  (
    'cfg_MTS004',
    'config',
    'MANAGER_TASK_PRIORITY_SORT_ORDER',
    'text',
    'critical=10;high=20;normal=30;low=40;backlog=50;then_deadline_at_utc;then_created_at_utc;then_request_id',
    'trading-manager/docs/95_task_system.md',
    'task_system;task_summary;priority_ordering',
    'sync_artifact',
    'Canonical sort order for global task summary queries.'
  ),
  (
    'cfg_MTS005',
    'config',
    'MANAGER_GLOBAL_TASK_SUMMARY_VIEW',
    'text',
    'trading_manager.task_summary',
    'trading-manager/docs/95_task_system.md',
    'task_system;global_task_summary;durable_sql;read_model',
    'sync_artifact',
    'Read-only global task summary view over manager_request, run_manifest, artifact_ref, and ready_signal. It derives current task status and exposes priority_rank for ordered dashboards/CLIs.'
  ),
  (
    'scr_MTS003',
    'script',
    'MANAGER_TASK_SUMMARY_LIST',
    'command',
    'PYTHONPATH=src python3 scripts/tasks/list_task_summary.py',
    '/root/projects/trading-manager/scripts/tasks/list_task_summary.py',
    'task_system;global_task_summary;task_status;priority_ordering',
    'sync_artifact',
    'List global manager task summary rows sorted by priority, deadline, creation time, and request id.'
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
