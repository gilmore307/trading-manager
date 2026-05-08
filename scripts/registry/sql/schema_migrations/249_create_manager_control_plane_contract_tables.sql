-- Create minimal manager control-plane contract tables and register concise MVP vocabulary.
-- SQL owns durable audit state; bulky payloads remain storage artifacts referenced by URI/hash.

CREATE SCHEMA IF NOT EXISTS trading_manager;

CREATE TABLE IF NOT EXISTS trading_manager.manager_request (
  request_id TEXT PRIMARY KEY,
  contract_type TEXT NOT NULL DEFAULT 'manager_request_v1' CHECK (contract_type = 'manager_request_v1'),
  request_kind TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'requested',
  created_at_utc TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  requested_by TEXT NOT NULL,
  target_component_id TEXT NOT NULL,
  target_component_kind TEXT,
  target_repo_id TEXT NOT NULL,
  target_version_ref TEXT,
  target_entrypoint_ref TEXT,
  expected_outputs JSONB NOT NULL DEFAULT '[]'::JSONB,
  policy_refs JSONB NOT NULL DEFAULT '[]'::JSONB,
  priority TEXT,
  deadline_at_utc TIMESTAMPTZ,
  idempotency_key TEXT UNIQUE,
  parent_request_id TEXT REFERENCES trading_manager.manager_request(request_id),
  parameter_ref TEXT,
  dry_run BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS idx_manager_request_status
ON trading_manager.manager_request(status);

CREATE INDEX IF NOT EXISTS idx_manager_request_created_at
ON trading_manager.manager_request(created_at_utc);

CREATE TABLE IF NOT EXISTS trading_manager.run_manifest (
  run_id TEXT PRIMARY KEY,
  contract_type TEXT NOT NULL DEFAULT 'run_manifest_v1' CHECK (contract_type = 'run_manifest_v1'),
  request_id TEXT NOT NULL REFERENCES trading_manager.manager_request(request_id),
  component_id TEXT NOT NULL,
  component_kind TEXT,
  repo_id TEXT NOT NULL,
  version_ref TEXT,
  entrypoint_ref TEXT,
  status TEXT NOT NULL DEFAULT 'running',
  started_at_utc TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  ended_at_utc TIMESTAMPTZ,
  environment_ref TEXT,
  parameter_ref TEXT,
  error_summary TEXT,
  retry_of_run_id TEXT REFERENCES trading_manager.run_manifest(run_id),
  checkpoint_ref TEXT
);

CREATE INDEX IF NOT EXISTS idx_run_manifest_request
ON trading_manager.run_manifest(request_id);

CREATE INDEX IF NOT EXISTS idx_run_manifest_status
ON trading_manager.run_manifest(status);

CREATE TABLE IF NOT EXISTS trading_manager.input_binding (
  binding_id TEXT PRIMARY KEY,
  contract_type TEXT NOT NULL DEFAULT 'input_binding_v1' CHECK (contract_type = 'input_binding_v1'),
  request_id TEXT REFERENCES trading_manager.manager_request(request_id),
  run_id TEXT REFERENCES trading_manager.run_manifest(run_id),
  input_role TEXT NOT NULL,
  input_ref TEXT NOT NULL,
  available_at_utc TIMESTAMPTZ,
  as_of_utc TIMESTAMPTZ,
  version_ref TEXT,
  entity_scope TEXT,
  time_window TEXT,
  schema_ref TEXT,
  quality_ref TEXT,
  lineage_ref TEXT,
  CHECK (request_id IS NOT NULL OR run_id IS NOT NULL)
);

CREATE INDEX IF NOT EXISTS idx_input_binding_request
ON trading_manager.input_binding(request_id);

CREATE INDEX IF NOT EXISTS idx_input_binding_run
ON trading_manager.input_binding(run_id);

CREATE TABLE IF NOT EXISTS trading_manager.run_step (
  step_id TEXT PRIMARY KEY,
  contract_type TEXT NOT NULL DEFAULT 'run_step_v1' CHECK (contract_type = 'run_step_v1'),
  run_id TEXT NOT NULL REFERENCES trading_manager.run_manifest(run_id),
  step_name TEXT NOT NULL,
  step_order INTEGER NOT NULL,
  status TEXT NOT NULL DEFAULT 'running',
  started_at_utc TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  ended_at_utc TIMESTAMPTZ,
  error_summary TEXT,
  UNIQUE (run_id, step_order)
);

CREATE INDEX IF NOT EXISTS idx_run_step_run
ON trading_manager.run_step(run_id);

CREATE TABLE IF NOT EXISTS trading_manager.artifact_ref (
  artifact_id TEXT PRIMARY KEY,
  contract_type TEXT NOT NULL DEFAULT 'artifact_ref_v1' CHECK (contract_type = 'artifact_ref_v1'),
  artifact_kind TEXT NOT NULL,
  producer_run_id TEXT NOT NULL REFERENCES trading_manager.run_manifest(run_id),
  uri TEXT NOT NULL,
  content_hash TEXT,
  created_at_utc TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  schema_ref TEXT NOT NULL,
  byte_size BIGINT,
  row_count BIGINT,
  retention_policy_ref TEXT,
  lifecycle_status TEXT NOT NULL DEFAULT 'active',
  media_type TEXT
);

CREATE INDEX IF NOT EXISTS idx_artifact_ref_run
ON trading_manager.artifact_ref(producer_run_id);

CREATE INDEX IF NOT EXISTS idx_artifact_ref_status
ON trading_manager.artifact_ref(lifecycle_status);

CREATE TABLE IF NOT EXISTS trading_manager.ready_signal (
  ready_signal_id TEXT PRIMARY KEY,
  contract_type TEXT NOT NULL DEFAULT 'ready_signal_v1' CHECK (contract_type = 'ready_signal_v1'),
  signal_kind TEXT NOT NULL,
  producer_component_id TEXT NOT NULL,
  producer_run_id TEXT NOT NULL REFERENCES trading_manager.run_manifest(run_id),
  artifact_refs TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
  status TEXT NOT NULL,
  created_at_utc TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  consumer_hint TEXT,
  blocking_reason TEXT,
  supersedes_ready_signal_id TEXT REFERENCES trading_manager.ready_signal(ready_signal_id),
  review_required BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_ready_signal_run
ON trading_manager.ready_signal(producer_run_id);

CREATE INDEX IF NOT EXISTS idx_ready_signal_status
ON trading_manager.ready_signal(status);

UPDATE trading_registry
SET payload = 'component_ref_v1;manager_request_v1;input_binding_v1;run_manifest_v1;run_step_v1;artifact_ref_v1;ready_signal_v1',
    path = 'trading-manager/docs/93_contracts.md',
    applies_to = 'trading-manager;trading-storage;control_plane;mvp_contracts;durable_sql;retention_managed_storage',
    artifact_sync_policy = 'sync_artifact',
    note = 'Accepted MVP manager/control-plane contract inventory. SQL stores durable request/input/run/step/artifact-ref/ready-signal facts; storage keeps bulky retention-managed payloads; component_ref_v1 is registry-backed fields until a component catalog is justified.',
    updated_at = NOW()
WHERE key = 'MANAGER_STORAGE_HANDOFF_CONTRACTS';

UPDATE trading_registry
SET payload = 'contract_type;request_id;request_kind;created_at_utc;requested_by;target_component_id;target_repo_id;expected_outputs;policy_refs;status',
    path = 'trading-manager/docs/93_contracts.md',
    applies_to = 'manager_request_v1;trading_manager.manager_request;control_plane;durable_sql',
    note = 'Concise required logical fields for manager_request_v1. Optional policy, priority, parent, parameter, and dry-run fields remain table columns without bloating the required contract.'
WHERE key = 'MANAGER_REQUEST_V1_REQUIRED_FIELDS';

UPDATE trading_registry
SET payload = 'contract_type;run_id;request_id;component_id;repo_id;status;started_at_utc;ended_at_utc',
    path = 'trading-manager/docs/93_contracts.md',
    applies_to = 'run_manifest_v1;trading_manager.run_manifest;control_plane;durable_sql',
    note = 'Concise required logical fields for run_manifest_v1. Large logs and detailed outputs remain artifact_ref_v1 payload references.'
WHERE key = 'RUN_MANIFEST_V1_REQUIRED_FIELDS';

UPDATE trading_registry
SET payload = 'contract_type;artifact_id;artifact_kind;producer_run_id;uri;created_at_utc;schema_ref;lifecycle_status',
    path = 'trading-manager/docs/93_contracts.md',
    applies_to = 'artifact_ref_v1;trading_manager.artifact_ref;control_plane;durable_sql;retention_managed_storage',
    note = 'Concise required logical fields for artifact_ref_v1. SQL stores durable reference metadata only; artifact bytes stay in storage.'
WHERE key = 'ARTIFACT_REF_V1_REQUIRED_FIELDS';

UPDATE trading_registry
SET payload = 'contract_type;ready_signal_id;signal_kind;producer_component_id;producer_run_id;artifact_refs;status;created_at_utc',
    path = 'trading-manager/docs/93_contracts.md',
    applies_to = 'ready_signal_v1;trading_manager.ready_signal;control_plane;durable_sql',
    note = 'Concise required logical fields for ready_signal_v1. Ready signals assert consumability, not promotion or activation approval.'
WHERE key = 'READY_SIGNAL_V1_REQUIRED_FIELDS';

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'cfg_MSH009',
    'config',
    'INPUT_BINDING_V1_REQUIRED_FIELDS',
    'text',
    'contract_type;binding_id;input_role;input_ref;available_at_utc;as_of_utc;version_ref',
    'trading-manager/docs/93_contracts.md',
    'input_binding_v1;trading_manager.input_binding;control_plane;durable_sql;point_in_time_evidence',
    'sync_artifact',
    'Concise required logical fields for input_binding_v1. The SQL table links each binding to a request, a run, or both.'
  ),
  (
    'cfg_MSH010',
    'config',
    'RUN_STEP_V1_REQUIRED_FIELDS',
    'text',
    'contract_type;step_id;run_id;step_name;step_order;status;started_at_utc;ended_at_utc',
    'trading-manager/docs/93_contracts.md',
    'run_step_v1;trading_manager.run_step;control_plane;durable_sql;step_evidence',
    'sync_artifact',
    'Concise required logical fields for run_step_v1. Use only when step-level evidence matters.'
  ),
  (
    'cfg_MSH011',
    'config',
    'MANAGER_CONTRACT_SQL_TABLES',
    'text',
    'trading_manager.manager_request;trading_manager.input_binding;trading_manager.run_manifest;trading_manager.run_step;trading_manager.artifact_ref;trading_manager.ready_signal',
    'trading-manager/docs/93_contracts.md',
    'trading-manager;control_plane;durable_sql;mvp_contracts',
    'sync_artifact',
    'Minimal first implementation tables for durable manager/control-plane state. Component identity is stored as registry-backed fields, not a separate component catalog table.'
  )
ON CONFLICT (id) DO UPDATE
SET key = EXCLUDED.key,
    payload_format = EXCLUDED.payload_format,
    payload = EXCLUDED.payload,
    path = EXCLUDED.path,
    applies_to = EXCLUDED.applies_to,
    artifact_sync_policy = EXCLUDED.artifact_sync_policy,
    note = EXCLUDED.note,
    updated_at = NOW();

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  ('sts_MSH001', 'status_value', 'MANAGER_CONTRACT_STATUS_REQUESTED', 'text', 'requested', 'trading-manager/docs/93_contracts.md', 'manager_contract_lifecycle_status;manager_request_v1', 'registry_only', 'Manager request has been recorded but not started.'),
  ('sts_MSH002', 'status_value', 'MANAGER_CONTRACT_STATUS_RUNNING', 'text', 'running', 'trading-manager/docs/93_contracts.md', 'manager_contract_lifecycle_status;run_manifest_v1;run_step_v1', 'registry_only', 'Run or step is in progress.'),
  ('sts_MSH003', 'status_value', 'MANAGER_CONTRACT_STATUS_SUCCEEDED', 'text', 'succeeded', 'trading-manager/docs/93_contracts.md', 'manager_contract_lifecycle_status;run_manifest_v1;run_step_v1', 'registry_only', 'Run or step completed successfully.'),
  ('sts_MSH004', 'status_value', 'MANAGER_CONTRACT_STATUS_FAILED', 'text', 'failed', 'trading-manager/docs/93_contracts.md', 'manager_contract_lifecycle_status;run_manifest_v1;run_step_v1;ready_signal_v1', 'registry_only', 'Run, step, or signal failed.'),
  ('sts_MSH005', 'status_value', 'MANAGER_CONTRACT_STATUS_BLOCKED', 'text', 'blocked', 'trading-manager/docs/93_contracts.md', 'manager_contract_lifecycle_status;manager_request_v1;ready_signal_v1', 'registry_only', 'Work cannot proceed until a blocker is resolved.'),
  ('sts_MSH006', 'status_value', 'MANAGER_CONTRACT_STATUS_CANCELLED', 'text', 'cancelled', 'trading-manager/docs/93_contracts.md', 'manager_contract_lifecycle_status;manager_request_v1;run_manifest_v1;run_step_v1', 'registry_only', 'Work was cancelled before successful completion.'),
  ('sts_MSH007', 'status_value', 'MANAGER_CONTRACT_STATUS_READY', 'text', 'ready', 'trading-manager/docs/93_contracts.md', 'manager_contract_lifecycle_status;ready_signal_v1', 'registry_only', 'Output is explicitly ready for its declared consumer scope.'),
  ('sts_MSH008', 'status_value', 'MANAGER_CONTRACT_STATUS_PARTIAL', 'text', 'partial', 'trading-manager/docs/93_contracts.md', 'manager_contract_lifecycle_status;ready_signal_v1', 'registry_only', 'Only a reviewed partial output is consumable.'),
  ('sts_MSH009', 'status_value', 'MANAGER_CONTRACT_STATUS_SUPERSEDED', 'text', 'superseded', 'trading-manager/docs/93_contracts.md', 'manager_contract_lifecycle_status;ready_signal_v1;artifact_ref_v1', 'registry_only', 'A newer artifact or signal replaces this one.'),
  ('sts_MSH010', 'status_value', 'MANAGER_CONTRACT_STATUS_EXPIRED', 'text', 'expired', 'trading-manager/docs/93_contracts.md', 'manager_contract_lifecycle_status;artifact_ref_v1;ready_signal_v1', 'registry_only', 'Reference is past its retention or validity window.'),
  ('sts_MSH011', 'status_value', 'MANAGER_CONTRACT_STATUS_DELETED', 'text', 'deleted', 'trading-manager/docs/93_contracts.md', 'manager_contract_lifecycle_status;artifact_ref_v1', 'registry_only', 'Payload was deleted while durable reference metadata remains.')
ON CONFLICT (id) DO UPDATE
SET key = EXCLUDED.key,
    payload_format = EXCLUDED.payload_format,
    payload = EXCLUDED.payload,
    path = EXCLUDED.path,
    applies_to = EXCLUDED.applies_to,
    artifact_sync_policy = EXCLUDED.artifact_sync_policy,
    note = EXCLUDED.note,
    updated_at = NOW();
