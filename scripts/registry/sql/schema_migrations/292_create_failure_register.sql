-- Create manager failure register and register failure-state policy.

CREATE TABLE IF NOT EXISTS trading_manager.failure_register (
  failure_id TEXT PRIMARY KEY,
  contract_type TEXT NOT NULL DEFAULT 'manager_failure_register_v1' CHECK (contract_type = 'manager_failure_register_v1'),
  request_id TEXT NOT NULL REFERENCES trading_manager.manager_request(request_id),
  run_id TEXT REFERENCES trading_manager.run_manifest(run_id),
  stage_id TEXT NOT NULL,
  target_component_id TEXT NOT NULL,
  source_id TEXT,
  symbol TEXT,
  start_month TEXT,
  end_month TEXT,
  failure_status TEXT NOT NULL CHECK (failure_status IN ('observed', 'agent_review_required', 'retry_required', 'corrected', 'accepted_skip', 'unresolved')),
  failure_kind TEXT NOT NULL,
  observed_status TEXT,
  error_summary TEXT,
  agent_review_ref TEXT,
  operator_approval_ref TEXT,
  correction_ref TEXT,
  skip_future_matching BOOLEAN NOT NULL DEFAULT FALSE,
  evidence_refs JSONB NOT NULL DEFAULT '[]'::JSONB,
  first_observed_at_utc TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at_utc TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  note TEXT,
  CHECK (failure_status NOT IN ('accepted_skip', 'corrected') OR agent_review_ref IS NOT NULL),
  CHECK (skip_future_matching = FALSE OR failure_status = 'accepted_skip')
);

CREATE INDEX IF NOT EXISTS idx_failure_register_request
ON trading_manager.failure_register(request_id);

CREATE INDEX IF NOT EXISTS idx_failure_register_stage_month_status
ON trading_manager.failure_register(stage_id, start_month, end_month, failure_status);

CREATE INDEX IF NOT EXISTS idx_failure_register_skip
ON trading_manager.failure_register(skip_future_matching)
WHERE skip_future_matching = TRUE;

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'cfg_MGRFAILREG001',
    'config',
    'MANAGER_FAILURE_REGISTER_CONTRACT',
    'text',
    'manager_failure_register_v1;observed;agent_review_required;retry_required;corrected;accepted_skip;unresolved;skip_future_matching',
    'trading-manager/docs/95_task_system.md',
    'trading_manager.failure_register;manager_stage_coverage_v1;manager_provider_dispatch_summary_v1',
    'sync_artifact',
    'Durable register for failed manager/component requests. All failures should be registered with current state. Correctable failures can move to corrected after agent-reviewed fix evidence. Expected historical absences can move to accepted_skip and may be skipped on future matching requests while preserving failure history.'
  ),
  (
    'scr_MGRFAILREG001',
    'script',
    'MANAGER_FAILURE_REGISTER_WRITE',
    'text',
    'python3 scripts/tasks/register_failure.py',
    'trading-manager/scripts/tasks/register_failure.py',
    'manager_failure_register_v1;trading_manager.failure_register',
    'sync_artifact',
    'Validate or persist manager failure-register rows.'
  ),
  (
    'scr_MGRFAILREG002',
    'script',
    'MANAGER_FAILURE_REGISTER_LIST',
    'text',
    'python3 scripts/tasks/list_failure_register.py',
    'trading-manager/scripts/tasks/list_failure_register.py',
    'manager_failure_register_v1;trading_manager.failure_register',
    'sync_artifact',
    'List manager failure-register rows.'
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
