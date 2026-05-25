-- Register the fold-scoped Layer 4 event-observation materializer and remove
-- the old Layer 10 input materializer from the active pre-replay workflow scope.

UPDATE trading_registry
SET applies_to = 'manager_layer_ten_event_risk_governor_input_materialization;layer_10_event_risk_governor;source_10_event_risk_governor;legacy_regeneration_diagnostic',
    note = 'Legacy diagnostic materializer for source_10 / Layer 10 event-risk rows. It is not part of the active pre-replay model_training_workflow; current Layer 10 starts after concentrated replay using replay failure/residual attribution evidence.',
    updated_at = NOW()
WHERE id = 'scr_L9ERGMAT001';

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'scr_L4EVOBS001',
    'script',
    'MANAGER_MATERIALIZE_LAYER_FOUR_EVENT_OBSERVATION_INPUTS',
    'command',
    'PYTHONPATH=src python3 scripts/tasks/materialize_layer_four_event_observation_inputs.py --start-month ${START_MONTH} --end-month ${END_MONTH} --write',
    '/root/projects/trading-manager/scripts/tasks/materialize_layer_four_event_observation_inputs.py',
    'manager_layer_04_event_observation_materialization;layer_04_event_failure_risk;event_observation_fold_panel;model_training_workflow;foundation_substrate',
    'sync_artifact',
    'Callable manager entrypoint that validates and materializes the fold-scoped Layer 4 global/sector event-observation substrate before concentrated replay. It performs no provider calls, model activation, broker execution, or storage lifecycle mutation.'
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
