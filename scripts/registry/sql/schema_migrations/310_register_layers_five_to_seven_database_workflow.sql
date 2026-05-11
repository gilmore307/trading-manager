-- Register SQL-backed safe offline workflow support for Layers 5-7.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'scr_L5DB001',
    'script',
    'MODEL_05_ALPHA_CONFIDENCE_DATABASE_GENERATION',
    'command',
    'PYTHONPATH=/root/projects/trading-model/src python3 /root/projects/trading-model/scripts/models/model_05_alpha_confidence/generate_model_05_alpha_confidence.py --from-database --source-start ${START_MONTH_START_ET} --source-end ${END_MONTH_EXCLUSIVE_START_ET} --output-jsonl /root/projects/trading-model/storage/runtime/model_05_alpha_confidence/model_rows_${START_MONTH}.jsonl',
    '/root/projects/trading-model/scripts/models/model_05_alpha_confidence/generate_model_05_alpha_confidence.py',
    'model_05_alpha_confidence;alpha_confidence_model;database_workflow;safe_offline_model_training',
    'sync_artifact',
    'Layer 5 SQL-backed generator reads completed Layer 4 and upstream model rows and persists trading_model.model_05_alpha_confidence without provider calls, model activation, broker execution, or storage lifecycle mutation.'
  ),
  (
    'scr_L6DB001',
    'script',
    'MODEL_06_POSITION_PROJECTION_DATABASE_GENERATION',
    'command',
    'PYTHONPATH=/root/projects/trading-model/src python3 /root/projects/trading-model/scripts/models/model_06_position_projection/generate_model_06_position_projection.py --from-database --source-start ${START_MONTH_START_ET} --source-end ${END_MONTH_EXCLUSIVE_START_ET} --output-jsonl /root/projects/trading-model/storage/runtime/model_06_position_projection/model_rows_${START_MONTH}.jsonl',
    '/root/projects/trading-model/scripts/models/model_06_position_projection/generate_model_06_position_projection.py',
    'model_06_position_projection;position_projection_model;database_workflow;safe_offline_model_training',
    'sync_artifact',
    'Layer 6 SQL-backed generator reads completed Layer 5 alpha-confidence rows and persists trading_model.model_06_position_projection using flat/no-pending position context defaults; it performs no provider calls, model activation, broker execution, or storage lifecycle mutation.'
  ),
  (
    'scr_L7DB001',
    'script',
    'MODEL_07_UNDERLYING_ACTION_DATABASE_GENERATION',
    'command',
    'PYTHONPATH=/root/projects/trading-model/src python3 /root/projects/trading-model/scripts/models/model_07_underlying_action/generate_model_07_underlying_action.py --from-database --source-start ${START_MONTH_START_ET} --source-end ${END_MONTH_EXCLUSIVE_START_ET} --output-jsonl /root/projects/trading-model/storage/runtime/model_07_underlying_action/model_rows_${START_MONTH}.jsonl',
    '/root/projects/trading-model/scripts/models/model_07_underlying_action/generate_model_07_underlying_action.py',
    'model_07_underlying_action;underlying_action_model;database_workflow;safe_offline_model_training',
    'sync_artifact',
    'Layer 7 SQL-backed generator reads completed Layer 5/6 rows and persists trading_model.model_07_underlying_action using local point-in-time default quote/liquidity/risk context; it remains offline planning only and performs no provider calls, model activation, broker execution, or storage lifecycle mutation.'
  ),
  (
    'term_L5L7DB001',
    'term',
    'LAYERS_FIVE_TO_SEVEN_DATABASE_OFFLINE_WORKFLOW',
    'text',
    'layers_05_06_07_database_safe_offline_workflow_v1',
    'trading-manager/docs/95_task_system.md',
    'model_05_alpha_confidence;model_06_position_projection;model_07_underlying_action;manager_stage_execution_summary_v1',
    'sync_artifact',
    'Manager-safe offline workflow for Layers 5-7 after upstream Layer 4 completes. Generation/evaluation/review stages may run without provider approval because provider_calls=0, activation=false, broker_execution=false, and promotion review remains deferred unless separately approved.'
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
