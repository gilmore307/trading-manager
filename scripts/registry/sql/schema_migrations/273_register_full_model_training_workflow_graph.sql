-- Register full Layer 1-8 historical model-training workflow graph.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'art_MMTW001',
    'artifact_type',
    'MANAGER_MODEL_TRAINING_WORKFLOW_PLAN_V1',
    'text',
    'manager_model_training_workflow_plan_v1',
    'trading-manager/src/trading_manager_tasks/model_training_workflow.py',
    'trading-manager;scheduler;historical_training;layer_01_market_regime;layer_02_sector_context;layer_03_target_state_vector;layer_04_event_overlay;layer_05_alpha_confidence;layer_06_position_projection;layer_07_underlying_action;layer_08_option_expression',
    'sync_artifact',
    'Full manager-owned historical model-training workflow graph for Layers 1-8. Defines data acquisition, feature/input generation, model generation, model evaluation, promotion-review preparation, and maintenance stages while preserving provider/model/broker gates.'
  ),
  (
    'scr_MMTW001',
    'script',
    'MANAGER_MODEL_TRAINING_WORKFLOW_PLAN',
    'text',
    'PYTHONPATH=src python3 scripts/tasks/plan_model_training_workflow.py',
    'trading-manager/scripts/tasks/plan_model_training_workflow.py',
    'trading-manager;scheduler;historical_training;manager_model_training_workflow_plan_v1',
    'sync_artifact',
    'Prints the current Layer 1-8 manager historical-training workflow graph and next gated stage without provider calls, model activation, or broker execution.'
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
