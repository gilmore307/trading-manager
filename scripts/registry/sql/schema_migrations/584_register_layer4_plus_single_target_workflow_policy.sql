-- Register the Layer 4+ single-target workflow boundary.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'cfg_L4SINGLETARGET001',
    'config',
    'LAYER_04_PLUS_SINGLE_TARGET_WORKFLOW_POLICY',
    'text',
    'layer_04_plus_single_target_interface_multiple_targets_require_separate_workflows',
    'trading-manager/src/trading_manager_tasks/model_training_workflow.py;trading-manager/docs/02_architecture.md;trading-model/docs/02_architecture.md',
    'historical_scheduler;model_training_workflow;layer_04_plus;target_symbol',
    'sync_artifact',
    'Layer 4 and later keep a single selected target per workflow run. If Layer 3 or a replay candidate policy emits multiple target symbols, manager schedules separate target-scoped workflow runs instead of passing a multi-target batch into Layer 4+ model interfaces.'
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
