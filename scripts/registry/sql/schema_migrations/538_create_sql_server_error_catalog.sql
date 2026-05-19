-- Move server error catalog facts into the manager SQL control plane.

CREATE TABLE IF NOT EXISTS trading_manager.server_error_catalog (
  catalog_row_id TEXT PRIMARY KEY,
  contract_type TEXT NOT NULL CHECK (contract_type IN ('server_error_catalog_entry', 'server_error_catalog_occurrence')),
  schema_version TEXT NOT NULL DEFAULT '1' CHECK (schema_version = '1'),
  error_number INTEGER NOT NULL CHECK (error_number >= 1),
  error_ref TEXT NOT NULL,
  error_fingerprint TEXT NOT NULL,
  request_id TEXT NOT NULL UNIQUE,
  duplicate_of_request_id TEXT,
  request_path TEXT NOT NULL,
  diagnosis_path TEXT NOT NULL,
  source_component TEXT NOT NULL,
  source_repo TEXT,
  error_scope TEXT NOT NULL,
  error_kind TEXT NOT NULL,
  severity TEXT NOT NULL CHECK (severity IN ('info', 'warning', 'error', 'critical')),
  summary TEXT NOT NULL,
  exit_code INTEGER,
  occurred_at_utc TIMESTAMPTZ NOT NULL,
  first_seen_at_utc TIMESTAMPTZ,
  last_seen_at_utc TIMESTAMPTZ,
  created_at_utc TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  deduplicated BOOLEAN NOT NULL DEFAULT FALSE,
  dedup_window_seconds INTEGER NOT NULL DEFAULT 3600 CHECK (dedup_window_seconds >= 0),
  catalog_payload_json JSONB NOT NULL DEFAULT '{}'::JSONB,
  updated_at_utc TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CHECK (error_ref = ('ERR-' || lpad(error_number::TEXT, 6, '0'))),
  CHECK (contract_type <> 'server_error_catalog_occurrence' OR duplicate_of_request_id IS NOT NULL),
  CHECK (contract_type <> 'server_error_catalog_entry' OR deduplicated = FALSE)
);

CREATE INDEX IF NOT EXISTS idx_server_error_catalog_error_ref
ON trading_manager.server_error_catalog(error_ref);

CREATE INDEX IF NOT EXISTS idx_server_error_catalog_fingerprint_time
ON trading_manager.server_error_catalog(error_fingerprint, occurred_at_utc DESC);

CREATE INDEX IF NOT EXISTS idx_server_error_catalog_component_status
ON trading_manager.server_error_catalog(source_component, severity, created_at_utc DESC);

UPDATE trading_registry
SET path = 'trading_manager.server_error_catalog',
    applies_to = 'trading_manager.server_error_catalog;server_wide_agent_error_handoff;human_error_number;owner_followup;discord_alert',
    note = 'SQL catalog row assigning each server error a human-facing number such as ERR-000001 while preserving the stable machine request id. Storage artifacts hold request, diagnosis, stdout, and stderr evidence only.'
WHERE key = 'SERVER_ERROR_CATALOG_ENTRY';

UPDATE trading_registry
SET path = 'trading_manager.server_error_catalog',
    applies_to = 'trading_manager.server_error_catalog;server_wide_agent_error_handoff;deduplication;human_error_number;discord_alert',
    note = 'SQL occurrence row for a duplicate server error within the dedup window. It reuses the original ERR number rather than allocating a new owner-facing error.'
WHERE key = 'SERVER_ERROR_CATALOG_OCCURRENCE';

UPDATE trading_registry
SET payload = 'PYTHONPATH=src python3 scripts/tasks/list_agent_errors.py --catalog-storage sql --limit 50',
    applies_to = 'trading_manager.server_error_catalog;server_wide_agent_error_handoff;server_error_catalog_entry;owner_followup',
    note = 'Lists recent SQL-backed server error catalog rows by human-facing error number and can filter by --error-ref ERR-000001.'
WHERE key = 'MANAGER_AGENT_ERROR_CATALOG_LIST';

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'cfg_AGENTERR008',
    'config',
    'MANAGER_AGENT_ERROR_SQL_CATALOG_POLICY',
    'text',
    'server_error_catalog_sql_primary;request_and_diagnosis_artifacts_remain_storage_refs;legacy_jsonl_read_compatibility_only',
    'trading-manager/src/trading_manager_tasks/agent_error_handler.py',
    'trading_manager.server_error_catalog;server_error_catalog_entry;server_error_catalog_occurrence;manager_failure_register',
    'sync_artifact',
    'Server error catalog numbering, deduplication, and owner follow-up facts are SQL control-plane rows. Storage/runtime files are evidence artifacts, not the canonical catalog.'
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
