-- Register realtime feature snapshots and historical-model decision input handoff scaffold.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'trm_EXEC_RT006',
    'term',
    'REALTIME_FEATURE_SNAPSHOT',
    'text',
    'realtime_feature_snapshot_v1',
    'trading-execution/src/trading_execution/market_data/features.py',
    'trading-execution;realtime_market_data;feature_snapshot;layers_1_8;historical_feature_parity;no_provider_calls;no_model_activation',
    'sync_artifact',
    'Side-effect-free realtime feature snapshot envelope. It maps realtime capture refs into Layer 1-8 feature refs with point-in-time timing, historical feature parity refs, frozen model config refs, and historical dataset snapshot refs without provider calls, persistence, or model activation.'
  ),
  (
    'trm_EXEC_RT007',
    'term',
    'REALTIME_FEATURE_SNAPSHOT_VALIDATION',
    'text',
    'realtime_feature_snapshot_validation_v1',
    'trading-execution/src/trading_execution/market_data/features.py',
    'trading-execution;realtime_feature_snapshot_v1;feature_time;available_time;tradeable_time;layers_1_8;no_future_leakage',
    'sync_artifact',
    'Local validation result for realtime feature snapshots. It checks required fields, Layer 1-8 row coverage, accepted dataset role, forbidden actions, parseable timing, and feature_time <= available_time <= tradeable_time.'
  ),
  (
    'trm_EXEC_RT008',
    'term',
    'EXECUTION_MODEL_DECISION_INPUT_SNAPSHOT',
    'text',
    'execution_model_decision_input_snapshot_v1',
    'trading-execution/src/trading_execution/market_data/features.py',
    'trading-execution;trading-model;historical_model_decision_handoff;model_decision_input;layers_1_8;no_model_activation;no_broker_calls',
    'sync_artifact',
    'Execution-side bridge from realtime feature snapshots to historical model data decision inputs. It packages all Layer 1-8 feature refs and frozen historical model/data refs for fixture or shadow decision routing without activating models or constructing orders.'
  ),
  (
    'trm_EXEC_RT009',
    'term',
    'EXECUTION_MODEL_DECISION_INPUT_VALIDATION',
    'text',
    'execution_model_decision_input_validation_v1',
    'trading-execution/src/trading_execution/market_data/features.py',
    'trading-execution;execution_model_decision_input_snapshot_v1;validation;layers_1_8;no_model_activation;no_broker_mutation',
    'sync_artifact',
    'Local validation result for realtime-to-model decision input handoff envelopes. It checks all Layer 1-8 input refs and nested feature snapshot validation without model activation, provider calls, order construction, or account mutation.'
  ),
  (
    'scr_EXEC_RT003',
    'script',
    'EXECUTION_REALTIME_FEATURE_SNAPSHOT_BUILD',
    'command',
    'PYTHONPATH=src python3 scripts/execution/build_realtime_feature_snapshot.py',
    'trading-execution/scripts/execution/build_realtime_feature_snapshot.py',
    'trading-execution;realtime_feature_snapshot_v1;historical_feature_parity;fixture_replay;shadow_monitoring;no_provider_calls',
    'sync_artifact',
    'Builds realtime_feature_snapshot_v1 from capture refs, timing refs, historical dataset snapshot refs, and frozen model config refs without external calls or model activation.'
  ),
  (
    'scr_EXEC_RT004',
    'script',
    'EXECUTION_REALTIME_MODEL_INPUT_BUILD',
    'command',
    'PYTHONPATH=src python3 scripts/execution/build_realtime_model_input.py',
    'trading-execution/scripts/execution/build_realtime_model_input.py',
    'trading-execution;execution_model_decision_input_snapshot_v1;historical_model_decision_handoff;fixture_replay;shadow_monitoring;no_model_activation',
    'sync_artifact',
    'Builds execution_model_decision_input_snapshot_v1 from a realtime feature snapshot or request payload so fixture/shadow routing can hand data to the historical model decision stack.'
  ),
  (
    'scr_EXEC_RT005',
    'script',
    'EXECUTION_REALTIME_MODEL_INPUT_VALIDATE',
    'command',
    'PYTHONPATH=src python3 scripts/execution/validate_realtime_model_input.py ${SNAPSHOT_JSON}',
    'trading-execution/scripts/execution/validate_realtime_model_input.py',
    'trading-execution;realtime_feature_snapshot_v1;execution_model_decision_input_snapshot_v1;validation;no_model_activation',
    'sync_artifact',
    'Validates realtime feature snapshots and realtime-to-model decision input envelopes without provider calls, broker calls, model activation, persistence, or account mutation.'
  ),
  (
    'cfg_EXEC_RT005',
    'config',
    'EXECUTION_REALTIME_MODEL_DECISION_HANDOFF_POLICY',
    'text',
    'realtime_capture_to_feature_snapshot_to_model_decision_input;historical_feature_parity_required;frozen_model_config_ref_required;historical_dataset_snapshot_ref_required;fixture_or_shadow_only_until_model_activation_review;does_not_authorize_orders',
    'trading-execution/docs/09_realtime_data.md',
    'trading-execution;trading-model;realtime_feature_snapshot_v1;execution_model_decision_input_snapshot_v1;historical_model_decision_handoff;approval_gate',
    'sync_artifact',
    'Policy that realtime capture must be converted into parity-bound feature snapshots and model decision input envelopes before historical-model decision routing. The scaffold is fixture/shadow only and does not authorize model activation, provider streams, or orders.'
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
