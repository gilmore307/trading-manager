-- Register safe offline model-training stage executor.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'art_MMSE001',
    'artifact_type',
    'MANAGER_STAGE_EXECUTION_SUMMARY_V1',
    'text',
    'manager_stage_execution_summary_v1',
    'trading-manager/src/trading_manager_tasks/stage_executor.py',
    'trading-manager;manager_model_training_workflow_state_v1;component_completion_receipt;offline_feature_generation;offline_model_generation;offline_model_evaluation;promotion_review_preparation;maintenance',
    'sync_artifact',
    'Manager-side summary for executing one ready safe offline workflow stage. Records command, return code, logs, receipt path, and confirms zero provider calls, zero model activation, and zero broker execution.'
  ),
  (
    'scr_MMSE001',
    'script',
    'MANAGER_SAFE_OFFLINE_STAGE_EXECUTION',
    'text',
    'PYTHONPATH=src python3 scripts/tasks/execute_model_training_stage.py',
    'trading-manager/scripts/tasks/execute_model_training_stage.py',
    'trading-manager;manager_model_training_workflow_state_v1;component_completion_receipt;offline_feature_generation;offline_model_generation;offline_model_evaluation;promotion_review_preparation;maintenance',
    'sync_artifact',
    'Executes one ready safe offline workflow stage after scheduler gates, writes logs and a component receipt, and refuses provider-gated stages.'
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
