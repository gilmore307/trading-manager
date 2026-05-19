-- Repair id collisions from agent decision skill registration and move skill rows to unique ids.

UPDATE trading_registry
SET kind = 'config',
    key = 'EXECUTION_ACTIVE_MODEL_CONFIG_WRITE_POLICY',
    payload_format = 'text',
    payload = 'valid_shadow_cycle_selection_required;expected_previous_active_ref_required;new_active_config_ref_required;rollback_ref_required;write_window_ref_required;broker_account_mutation_forbidden',
    path = 'trading-execution/docs/40_runtime_model_lifecycle.md',
    applies_to = 'trading-execution;active_model_config;runtime_activation;rollback_ref',
    artifact_sync_policy = 'sync_artifact',
    note = 'Policy for the separate active pointer write gate. Selection and pointer mutation are distinct so the decision, write, and rollback path remain auditable.',
    updated_at = NOW()
WHERE id = 'cfg_EXECMLC002';

UPDATE trading_registry
SET kind = 'config',
    key = 'MANAGER_AGENT_ERROR_DEDUP_POLICY',
    payload_format = 'text',
    payload = 'fingerprint_excludes_occurrence_time_and_log_paths;dedup_window_seconds=3600;duplicate_notifications_suppressed_by_default',
    path = 'trading-manager/src/trading_manager_tasks/agent_error_handler.py',
    applies_to = 'server_wide_agent_error_handoff;deduplication;discord_alert;owner_visibility',
    artifact_sync_policy = 'sync_artifact',
    note = 'Repeated errors with the same fingerprint inside the dedup window reuse the same ERR number and suppress duplicate Discord notifications unless explicitly overridden.',
    updated_at = NOW()
WHERE id = 'cfg_AGENTERR005';

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'cfg_AGENTSKILL002',
    'config',
    'RUNTIME_MODEL_LIFECYCLE_REVIEW_SKILL',
    'text',
    'runtime-model-lifecycle-review',
    '/root/.openclaw/workspace/skills/openclaw/runtime-model-lifecycle-review/SKILL.md',
    'trading-execution;runtime_model_lifecycle;shadow_cycle_selection;active_shadow_model_comparison;execution_active_model_config_write',
    'registry_only',
    'Workspace skill for execution-owned market-hours shadow-cycle roster review. It requires blinded model labels and returns active/realtime/shadow/eliminate recommendations without writing active pointers or mutating broker/account state.'
  ),
  (
    'cfg_AGENTSKILL004',
    'config',
    'SERVER_ERROR_DIAGNOSIS_SKILL',
    'text',
    'server-error-diagnosis',
    '/root/.openclaw/workspace/skills/openclaw/server-error-diagnosis/SKILL.md',
    'server_wide_agent_error_handoff;server_error_agent_request;agent_error_diagnosis;safe_repair',
    'registry_only',
    'Workspace skill for bounded server error diagnosis and safe internal repair. It forbids provider calls, broker/account mutation, secret disclosure, and durable data deletion without a separate gate.'
  )
ON CONFLICT (id) DO UPDATE SET
  kind = EXCLUDED.kind,
  key = EXCLUDED.key,
  payload_format = EXCLUDED.payload_format,
  payload = EXCLUDED.payload,
  path = EXCLUDED.path,
  applies_to = EXCLUDED.applies_to,
  artifact_sync_policy = EXCLUDED.artifact_sync_policy,
  note = EXCLUDED.note,
  updated_at = NOW();

UPDATE trading_registry
SET payload = 'active_model_primary;promoted_not_active_shadow_during_market_hours;cycle_duration_about_one_month;anonymous_model_comparison_required;ranks_2_to_4_realtime_candidates;eliminate_requires_sufficient_reason;repeated_eliminate_can_retire;active_pointer_write_requires_separate_gate',
    note = 'Execution policy for runtime model lifecycle: active model remains trading authority, promoted candidates run shadow, mature cycle evidence is reviewed with anonymous model labels, and the active config pointer write requires a separate audited gate.',
    updated_at = NOW()
WHERE key = 'EXECUTION_RUNTIME_MODEL_LIFECYCLE_POLICY';

UPDATE trading_registry
SET note = 'Unified manager-owned handoff for server-side component errors that need agent diagnosis or safe repair. Reviewer agents must use the server-error-diagnosis skill; the handoff is not model-training-specific.',
    updated_at = NOW()
WHERE key = 'SERVER_WIDE_AGENT_ERROR_HANDOFF';

