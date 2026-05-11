-- Register realtime decision-effectiveness monitoring aggregate.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'scr_EXEC_RT_EFFECT001',
    'script',
    'EXECUTION_REALTIME_DECISION_EFFECTIVENESS_AGGREGATE',
    'text',
    'PYTHONPATH=src python3 scripts/execution/aggregate_realtime_decision_effectiveness.py',
    'trading-execution/scripts/execution/aggregate_realtime_decision_effectiveness.py',
    'trading-execution;realtime_monitoring;decision_effectiveness;shadow_live_quality;no_historical_dataset_rows;no_model_activation;no_broker_mutation;no_account_mutation',
    'sync_artifact',
    'Aggregates matured realtime/shadow decision outcome records into realtime_model_decision_effectiveness_v1 without creating historical dataset rows, activating models, persisting state, or mutating broker/account state.'
  ),
  (
    'trm_RTEM001',
    'term',
    'REALTIME_MODEL_DECISION_EFFECTIVENESS',
    'text',
    'realtime_model_decision_effectiveness_v1',
    'trading-execution/src/trading_execution/market_data/effectiveness.py',
    'trading-execution;realtime_monitoring;decision_effectiveness;promotion_review_evidence;drift_review_evidence;trust_review_evidence',
    'sync_artifact',
    'Lightweight realtime/shadow model-quality monitoring aggregate. Summarizes matured decision correctness, accuracy, hit rate, status counts, model/layer/instrument counts, and invariant flags; not a historical test-set row source.'
  ),
  (
    'trm_EXEC_RT_EFFECT002',
    'term',
    'REALTIME_MODEL_DECISION_EFFECTIVENESS_ROW',
    'text',
    'realtime_model_decision_effectiveness_row_v1',
    'trading-execution/src/trading_execution/market_data/effectiveness.py',
    'trading-execution;realtime_monitoring;decision_effectiveness;matured_outcome;decision_correctness',
    'sync_artifact',
    'One summarized matured realtime/shadow decision outcome row containing decision id, model/layer, instrument, horizon, matured outcome ref, and correctness status.'
  ),
  (
    'cfg_EXEC_RT_EFFECT001',
    'config',
    'REALTIME_DECISION_EFFECTIVENESS_BOUNDARY',
    'text',
    'monitoring_aggregate_only;no_historical_dataset_row_creation;no_model_refit;no_model_activation;no_provider_calls;no_broker_calls;no_order_construction;no_persistence;no_account_mutation',
    'trading-execution/docs/09_realtime_data.md',
    'trading-execution;trading-manager;realtime_monitoring;decision_effectiveness;historical_pipeline_boundary',
    'sync_artifact',
    'Realtime decision-effectiveness aggregates may inform promotion/drift/trust review, but they do not replace historical dataset construction and must not activate models, providers, broker routes, persistence, or account mutation.'
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
