-- Register durable model-training workflow state and advance entrypoint.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'art_MMTW002',
    'artifact_type',
    'MANAGER_MODEL_TRAINING_WORKFLOW_STATE_V1',
    'text',
    'manager_model_training_workflow_state_v1',
    'trading-manager/src/trading_manager_tasks/model_training_state.py',
    'trading-manager;scheduler;historical_training;manager_model_training_workflow_plan_v1;component_completion_receipt',
    'sync_artifact',
    'Durable checkpoint for the manager-owned Layer 1-8 historical-training workflow. Records stage status, commands, blockers, approval refs, receipt refs, artifact refs, and next-stage progression.'
  ),
  (
    'scr_MMTW002',
    'script',
    'MANAGER_MODEL_TRAINING_WORKFLOW_ADVANCE',
    'text',
    'PYTHONPATH=src python3 scripts/tasks/advance_model_training_workflow.py',
    'trading-manager/scripts/tasks/advance_model_training_workflow.py',
    'trading-manager;scheduler;historical_training;manager_model_training_workflow_state_v1;component_completion_receipt',
    'sync_artifact',
    'Refreshes the durable Layer 1-8 workflow checkpoint, ingests component receipts, records reviewed approval refs, and selects the next safe or gated stage without provider calls, model activation, or broker execution.'
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
