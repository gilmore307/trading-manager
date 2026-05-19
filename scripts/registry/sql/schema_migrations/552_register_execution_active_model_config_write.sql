-- Register the explicit execution active-model config pointer write gate.

UPDATE trading_registry
SET note = 'Execution-owned active model config pointer after runtime shadow-cycle selection and execution_active_model_config_write. Evaluation produces promotion readiness only.',
    updated_at = NOW()
WHERE key = 'EXECUTION_ACTIVE_MODEL_CONFIG';

UPDATE trading_registry
SET payload = 'active_model_primary;promoted_not_active_shadow_during_market_hours;cycle_duration_about_one_month;ranks_2_to_4_realtime_candidates;eliminate_requires_sufficient_reason;repeated_eliminate_can_retire;active_pointer_write_requires_separate_gate',
    note = 'Execution policy for runtime activation: active model remains trading authority, promoted candidates run shadow, mature cycle evidence selects active/realtime/eliminate roles, and the active config pointer write requires a separate audited gate.',
    updated_at = NOW()
WHERE key = 'EXECUTION_RUNTIME_MODEL_LIFECYCLE_POLICY';

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'art_EXECMLC002',
    'artifact_type',
    'EXECUTION_ACTIVE_MODEL_CONFIG_WRITE',
    'text',
    'execution_active_model_config_write',
    'trading-execution/docs/40_runtime_model_lifecycle.md;trading-execution/src/trading_execution/model_lifecycle.py',
    'trading-execution;runtime_model_lifecycle;active_model_config;rollback_ref;pointer_write',
    'sync_artifact',
    'Audited execution-owned active model config pointer write after a valid execution_shadow_cycle_selection. It records expected previous active ref, new active config ref, rollback ref, and write window; it performs no broker/order/account mutation.'
  ),
  (
    'cfg_EXECMLC002',
    'config',
    'EXECUTION_ACTIVE_MODEL_CONFIG_WRITE_POLICY',
    'text',
    'valid_shadow_cycle_selection_required;expected_previous_active_ref_required;new_active_config_ref_required;rollback_ref_required;write_window_ref_required;broker_account_mutation_forbidden',
    'trading-execution/docs/40_runtime_model_lifecycle.md',
    'trading-execution;active_model_config;runtime_activation;rollback_ref',
    'sync_artifact',
    'Policy for the separate active pointer write gate. Selection and pointer mutation are distinct so the decision, write, and rollback path remain auditable.'
  ),
  (
    'scr_EXECMLC002',
    'script',
    'TRADING_EXECUTION_BUILD_ACTIVE_MODEL_CONFIG_WRITE',
    'command',
    'PYTHONPATH=src python3 scripts/execution/build_active_model_config_write.py --shadow-cycle-selection-json $SHADOW_CYCLE_SELECTION_JSON --expected-previous-active-model-ref $EXPECTED_PREVIOUS_ACTIVE_MODEL_REF --new-active-config-ref $NEW_ACTIVE_CONFIG_REF --rollback-ref $ROLLBACK_REF --write-window-ref $WRITE_WINDOW_REF',
    '/root/projects/trading-execution/scripts/execution/build_active_model_config_write.py',
    'trading-execution;execution_active_model_config_write;active_model_config;runtime_model_lifecycle',
    'sync_artifact',
    'Build an execution_active_model_config_write record from a valid shadow-cycle selection. The script records the active pointer write and rollback ref but constructs no orders, calls no brokers, and mutates no accounts.'
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
