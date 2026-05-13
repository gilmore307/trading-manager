-- Register durable human-facing error numbering for server-wide error handoffs.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'art_AGENTERR003',
    'artifact_type',
    'SERVER_ERROR_CATALOG_ENTRY',
    'text',
    'server_error_catalog_entry',
    'trading-manager/storage/runtime/agent_error_handling/server_error_catalog.jsonl',
    'server_wide_agent_error_handoff;human_error_number;owner_followup;discord_alert',
    'sync_artifact',
    'Append-only catalog row assigning each server error a human-facing number such as ERR-000001 while preserving the stable machine request id.'
  ),
  (
    'cfg_AGENTERR004',
    'config',
    'MANAGER_AGENT_ERROR_NUMBERING_POLICY',
    'text',
    'append_only_monotonic_error_ref_ERR_000001;request_id_remains_machine_stable_id;schema_version_carries_versioning',
    'trading-manager/src/trading_manager_tasks/agent_error_handler.py',
    'server_wide_agent_error_handoff;human_error_number;stable_id_policy',
    'sync_artifact',
    'Server errors receive monotonic owner-facing refs for chat follow-up. Business/storage ids remain stable semantic ids; versioning stays in schema_version.'
  ),
  (
    'scr_AGENTERR002',
    'script',
    'MANAGER_AGENT_ERROR_CATALOG_LIST',
    'command',
    'PYTHONPATH=src python3 scripts/tasks/list_agent_errors.py --limit 50',
    '/root/projects/trading-manager/scripts/tasks/list_agent_errors.py',
    'server_wide_agent_error_handoff;server_error_catalog_entry;owner_followup',
    'sync_artifact',
    'Lists recent server error catalog rows by human-facing error number and can filter by --error-ref ERR-000001.'
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
