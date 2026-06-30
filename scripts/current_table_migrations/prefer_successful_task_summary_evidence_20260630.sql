BEGIN;

CREATE OR REPLACE VIEW trading_manager.task_summary AS
WITH request_base AS (
  SELECT
    manager_request.request_id,
    manager_request.contract_type,
    manager_request.request_kind,
    manager_request.status AS request_status,
    manager_request.created_at_utc,
    manager_request.requested_by,
    manager_request.target_component_id,
    manager_request.target_component_kind,
    manager_request.target_repo_id,
    manager_request.expected_outputs,
    manager_request.policy_refs,
    COALESCE(NULLIF(lower(manager_request.priority), ''::text), 'normal'::text) AS priority,
    manager_request.deadline_at_utc,
    manager_request.parameter_ref,
    manager_request.dry_run
  FROM trading_manager.manager_request
),
prioritized AS (
  SELECT
    request_base.*,
    CASE request_base.priority
      WHEN 'critical'::text THEN 10
      WHEN 'high'::text THEN 20
      WHEN 'normal'::text THEN 30
      WHEN 'low'::text THEN 40
      WHEN 'backlog'::text THEN 50
      ELSE 30
    END AS priority_rank
  FROM request_base
)
SELECT
  r.request_id,
  r.contract_type,
  r.request_kind,
  COALESCE(effective_signal.status, effective_run.status, r.request_status) AS task_status,
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
  effective_run.run_id AS latest_run_id,
  effective_run.status AS latest_run_status,
  effective_run.started_at_utc AS latest_run_started_at_utc,
  effective_run.ended_at_utc AS latest_run_ended_at_utc,
  effective_run.error_summary AS latest_run_error_summary,
  effective_signal.ready_signal_id AS latest_ready_signal_id,
  effective_signal.status AS latest_ready_signal_status,
  effective_signal.review_required AS latest_ready_signal_review_required,
  effective_signal.blocking_reason AS latest_ready_signal_blocking_reason,
  COALESCE(artifact_counts.artifact_count, 0::bigint) AS artifact_count
FROM prioritized r
LEFT JOIN LATERAL (
  SELECT
    rm.run_id,
    rm.contract_type,
    rm.request_id,
    rm.component_id,
    rm.component_kind,
    rm.repo_id,
    rm.version_ref,
    rm.entrypoint_ref,
    rm.status,
    rm.started_at_utc,
    rm.ended_at_utc,
    rm.environment_ref,
    rm.parameter_ref,
    rm.error_summary,
    rm.retry_of_run_id,
    rm.checkpoint_ref
  FROM trading_manager.run_manifest rm
  WHERE rm.request_id = r.request_id
  ORDER BY
    CASE
      WHEN rm.status IN ('succeeded', 'success', 'completed', 'complete', 'ready') THEN 0
      ELSE 1
    END,
    rm.started_at_utc DESC,
    rm.run_id DESC
  LIMIT 1
) effective_run ON true
LEFT JOIN LATERAL (
  SELECT
    rs.ready_signal_id,
    rs.contract_type,
    rs.signal_kind,
    rs.producer_component_id,
    rs.producer_run_id,
    rs.artifact_refs,
    rs.status,
    rs.created_at_utc,
    rs.consumer_hint,
    rs.blocking_reason,
    rs.supersedes_ready_signal_id,
    rs.review_required
  FROM trading_manager.ready_signal rs
  JOIN trading_manager.run_manifest rm ON rm.run_id = rs.producer_run_id
  WHERE rm.request_id = r.request_id
    AND rs.supersedes_ready_signal_id IS NULL
  ORDER BY
    CASE
      WHEN rs.status = 'ready' THEN 0
      WHEN rs.status = 'partial' THEN 1
      ELSE 2
    END,
    rs.created_at_utc DESC,
    rs.ready_signal_id DESC
  LIMIT 1
) effective_signal ON true
LEFT JOIN LATERAL (
  SELECT count(*) AS artifact_count
  FROM trading_manager.artifact_ref ar
  JOIN trading_manager.run_manifest rm ON rm.run_id = ar.producer_run_id
  WHERE rm.request_id = r.request_id
) artifact_counts ON true;

COMMIT;
