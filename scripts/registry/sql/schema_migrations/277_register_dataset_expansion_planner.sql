-- Register manager-owned dataset expansion planner.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'art_MDSE001',
    'artifact_type',
    'MANAGER_DATASET_EXPANSION_PLAN_V1',
    'text',
    'manager_dataset_expansion_plan_v1',
    'trading-manager/src/trading_manager_tasks/dataset_expansion.py',
    'trading-manager;historical_training;dataset_expansion;model_dataset_snapshot;model_dataset_split;model_eval_label;model_eval_run',
    'sync_artifact',
    'Manager-owned plan selecting the next model layer and dataset role to expand: train, calibration, validation, test, forward holdout, or shadow monitoring. The plan preserves provider, model-activation, and broker-execution gates.'
  ),
  (
    'cfg_MDSE001',
    'config',
    'MANAGER_DATASET_EXPANSION_POLICY',
    'text',
    'manager_selects_next_dataset_role;layer_dependency_order;train_then_calibration_then_validation_then_test;forward_holdout_for_split_stability_drift_coverage;shadow_only_after_production_approval;provider_calls_require_live_call_approval_v1',
    'trading-manager/docs/100_dataset_expansion.md',
    'trading-manager;dataset_expansion;historical_training;promotion_readiness;live_call_approval_v1',
    'sync_artifact',
    'Dataset expansion policy: manager decides which layer/role to expand next, prepares only safe artifacts/payloads by default, and never treats expansion as provider-call approval, model activation, or broker execution.'
  ),
  (
    'scr_MDSE001',
    'script',
    'MANAGER_DATASET_EXPANSION_PLANNER',
    'text',
    'PYTHONPATH=src python3 scripts/tasks/plan_dataset_expansion.py',
    'trading-manager/scripts/tasks/plan_dataset_expansion.py',
    'trading-manager;manager_dataset_expansion_plan_v1;historical_training;dataset_expansion',
    'sync_artifact',
    'Plans the next manager-selected dataset expansion and, with --write, prepares selected safe artifacts/payloads without provider calls, model activation, or broker execution.'
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
