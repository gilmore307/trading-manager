-- Register trading-model realtime decision handoff route-plan scaffold.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'trm_MODEL_RTD001',
    'term',
    'MODEL_REALTIME_DECISION_INPUT_VALIDATION',
    'text',
    'model_realtime_decision_input_validation_v1',
    'trading-model/src/models/realtime_decision_handoff.py',
    'trading-model;trading-execution;execution_model_decision_input_snapshot_v1;layers_1_8;validation;no_model_activation;no_broker_calls',
    'sync_artifact',
    'Model-side validation for execution_model_decision_input_snapshot_v1 envelopes. It checks required fields, Layer 1-8 coverage, expected model ids/outputs, forbidden actions, and decision time without running models, calling providers, or constructing orders.'
  ),
  (
    'trm_MODEL_RTD002',
    'term',
    'MODEL_REALTIME_DECISION_ROUTE_PLAN',
    'text',
    'model_realtime_decision_route_plan_v1',
    'trading-model/src/models/realtime_decision_handoff.py',
    'trading-model;realtime_decision_handoff;historical_model_decision_route;fixture_replay;shadow_monitoring;layers_1_8;no_model_activation',
    'sync_artifact',
    'Model-side route plan that maps realtime execution decision input refs to reviewed Layer 1-8 model generator entrypoints for fixture/shadow historical-model decision routing. It does not execute generators, activate production configs, persist durable decisions, or authorize orders.'
  ),
  (
    'trm_MODEL_RTD003',
    'term',
    'MODEL_REALTIME_DECISION_ROUTE_PLAN_VALIDATION',
    'text',
    'model_realtime_decision_route_plan_validation_v1',
    'trading-model/src/models/realtime_decision_handoff.py',
    'trading-model;model_realtime_decision_route_plan_v1;validation;layers_1_8;no_provider_calls;no_model_activation',
    'sync_artifact',
    'Validation result for model_realtime_decision_route_plan_v1. It verifies all Layer 1-8 route rows and reviewed generator entrypoints without side effects.'
  ),
  (
    'scr_MODEL_RTD001',
    'script',
    'MODEL_REALTIME_DECISION_HANDOFF_PLAN',
    'command',
    'PYTHONPATH=src python3 scripts/models/plan_realtime_decision_handoff.py ${DECISION_INPUT_JSON}',
    'trading-model/scripts/models/plan_realtime_decision_handoff.py',
    'trading-model;model_realtime_decision_route_plan_v1;execution_model_decision_input_snapshot_v1;fixture_replay;shadow_monitoring',
    'sync_artifact',
    'Builds a model_realtime_decision_route_plan_v1 from an execution realtime model decision input snapshot. The script is local and does not run model generators or activate production configs.'
  ),
  (
    'scr_MODEL_RTD002',
    'script',
    'MODEL_REALTIME_DECISION_HANDOFF_VALIDATE',
    'command',
    'PYTHONPATH=src python3 scripts/models/validate_realtime_decision_handoff.py ${HANDOFF_JSON}',
    'trading-model/scripts/models/validate_realtime_decision_handoff.py',
    'trading-model;model_realtime_decision_input_validation_v1;model_realtime_decision_route_plan_validation_v1;no_model_activation',
    'sync_artifact',
    'Validates execution realtime decision input snapshots or model realtime route plans without provider calls, model activation, order construction, persistence, or account mutation.'
  ),
  (
    'cfg_MODEL_RTD001',
    'config',
    'MODEL_REALTIME_DECISION_HANDOFF_POLICY',
    'text',
    'execution_model_decision_input_snapshot_required;fixture_replay_or_shadow_monitoring_only;layer_1_8_route_coverage_required;no_generator_execution_by_route_plan;no_production_model_activation;no_order_authority',
    'trading-model/docs/98_realtime_decision_handoff.md',
    'trading-model;trading-execution;realtime_decision_handoff;historical_model_decision_route;approval_gate',
    'sync_artifact',
    'Policy that realtime execution inputs may enter trading-model only through explicit model decision input snapshots and route plans. Route plans are fixture/shadow only and do not authorize production model activation or execution.'
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
