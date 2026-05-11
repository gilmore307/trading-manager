-- Register local Layer 4 event-overlay input materialization.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'trm_L4EOM001',
    'term',
    'MANAGER_LAYER_FOUR_EVENT_OVERLAY_INPUT_MATERIALIZATION',
    'text',
    'manager_layer_four_event_overlay_input_materialization_v1',
    'trading-manager/docs/95_task_system.md',
    'layer_04_event_overlay;source_04_event_overlay;model_training_workflow;local_input_materialization',
    'sync_artifact',
    'Manager receipt for building Layer 4 event overview rows from local source-detector outputs over already-reviewed Layer 2 bar artifacts. It performs no provider calls, model activation, broker execution, or storage lifecycle mutation.'
  ),
  (
    'scr_L4EOM001',
    'script',
    'MANAGER_MATERIALIZE_LAYER_FOUR_EVENT_OVERLAY_INPUTS',
    'command',
    'PYTHONPATH=src python3 scripts/tasks/materialize_layer_four_event_overlay_inputs.py --start-month ${START_MONTH} --end-month ${END_MONTH} --write',
    '/root/projects/trading-manager/scripts/tasks/materialize_layer_four_event_overlay_inputs.py',
    'manager_layer_four_event_overlay_input_materialization_v1;layer_04_event_overlay;source_04_event_overlay;model_training_workflow',
    'sync_artifact',
    'Callable manager entrypoint that materializes source_04_event_overlay rows from local detector outputs over existing reviewed Layer 2 feed artifacts without provider dispatch.'
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
