-- Register the server-wide agent error diagnosis/repair handoff.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'term_AGENTERR001',
    'term',
    'SERVER_WIDE_AGENT_ERROR_HANDOFF',
    'text',
    'server_wide_agent_error_handoff',
    'trading-manager/src/trading_manager_tasks/agent_error_handler.py',
    'trading-manager;server_errors;agent_diagnosis;safe_repair;evidence_first',
    'sync_artifact',
    'Unified manager-owned handoff for any server-side component that needs agent diagnosis or safe repair after an observed error. The handoff is not model-training-specific.'
  ),
  (
    'art_AGENTERR001',
    'artifact_type',
    'SERVER_ERROR_AGENT_REQUEST',
    'text',
    'server_error_agent_request',
    'trading-manager/src/trading_manager_tasks/agent_error_handler.py',
    'server_wide_agent_error_handoff;agent_diagnosis;safe_repair;bounded_evidence',
    'sync_artifact',
    'Standard request artifact submitted after an error. It carries component/repo/scope, command, exit code, log/evidence refs, allowed actions, forbidden actions, and the agent prompt.'
  ),
  (
    'art_AGENTERR002',
    'artifact_type',
    'AGENT_ERROR_DIAGNOSIS',
    'text',
    'agent_error_diagnosis',
    'trading-manager/src/trading_manager_tasks/agent_error_handler.py',
    'server_error_agent_request;agent_diagnosis;repair_attempt;retry_recommendation',
    'sync_artifact',
    'Standard diagnosis artifact produced or queued by the server-wide agent error handoff. Queued artifacts are valid when no reviewed runner command is configured.'
  ),
  (
    'scr_AGENTERR001',
    'script',
    'MANAGER_AGENT_ERROR_HANDOFF_CALL',
    'command',
    'PYTHONPATH=src python3 scripts/tasks/call_agent_for_error.py --source-component ${SOURCE_COMPONENT} --summary ${SUMMARY}',
    '/root/projects/trading-manager/scripts/tasks/call_agent_for_error.py',
    'server_wide_agent_error_handoff;server_error_agent_request;agent_error_diagnosis;safe_repair',
    'sync_artifact',
    'Component-neutral entrypoint for creating server-wide error agent request/diagnosis artifacts. Actual agent runner invocation requires explicit reviewed runner configuration.'
  ),
  (
    'cfg_AGENTERR001',
    'config',
    'MANAGER_AGENT_ERROR_SAFETY_BOUNDARY',
    'text',
    'no_provider_calls_no_broker_or_account_mutation_no_secret_exfiltration_no_destructive_storage_or_service_changes_without_separate_approval',
    'trading-manager/src/trading_manager_tasks/agent_error_handler.py',
    'server_wide_agent_error_handoff;safety_boundary;agent_repair',
    'sync_artifact',
    'Central safety boundary for automated agent error diagnosis and repair. Internal reversible code/config/test/doc fixes are allowed; provider calls, broker/account mutation, secret exfiltration, destructive storage, service restarts, and package changes require a separate approval path.'
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
