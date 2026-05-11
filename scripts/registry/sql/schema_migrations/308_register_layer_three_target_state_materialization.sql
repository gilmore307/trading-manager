-- Register local Layer 3 target-state input materialization.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'trm_L3TSM001',
    'term',
    'MANAGER_LAYER_THREE_TARGET_STATE_INPUT_MATERIALIZATION',
    'text',
    'manager_layer_three_target_state_input_materialization_v1',
    'trading-manager/docs/95_task_system.md',
    'layer_03_target_state_vector;source_03_target_state;model_training_workflow;local_input_materialization',
    'sync_artifact',
    'Manager receipt for reusing already-approved Layer 2 Alpaca bar artifacts as local Layer 3 target-state source inputs. It performs no provider calls, model activation, broker execution, or storage lifecycle mutation.'
  ),
  (
    'scr_L3TSM001',
    'script',
    'MANAGER_MATERIALIZE_LAYER_THREE_TARGET_STATE_INPUTS',
    'command',
    'PYTHONPATH=src python3 scripts/tasks/materialize_layer_three_target_state_inputs.py --start-month ${START_MONTH} --end-month ${END_MONTH} --write',
    '/root/projects/trading-manager/scripts/tasks/materialize_layer_three_target_state_inputs.py',
    'manager_layer_three_target_state_input_materialization_v1;layer_03_target_state_vector;source_03_target_state;model_training_workflow',
    'sync_artifact',
    'Callable manager entrypoint that materializes source_03_target_state rows from existing reviewed Layer 2 feed artifacts without provider dispatch.'
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
