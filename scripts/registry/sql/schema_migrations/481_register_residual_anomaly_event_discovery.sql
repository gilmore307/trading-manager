-- Register Layer 8 residual-anomaly event discovery builder.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES (
  'scr_M8ERGRD001',
  'script',
  'MODEL_08_RESIDUAL_ANOMALY_EVENT_DISCOVERY_BUILD',
  'command',
  'PYTHONPATH=src python3 scripts/models/model_08_event_risk_governor/build_residual_anomaly_event_discovery.py',
  '/root/projects/trading-model/scripts/models/model_08_event_risk_governor/build_residual_anomaly_event_discovery.py;/root/projects/trading-model/src/models/model_08_event_risk_governor/residual_anomaly_event_discovery.py',
  'residual_anomaly_event_discovery_v1;residual_anomaly_event_discovery_summary_v1;event_family_strategy_promotion_review_packet_v1;model_08_event_risk_governor;event_observation_pool;event_strategy_promotion_review',
  'sync_artifact',
  'Builds the EventRiskGovernor residual-anomaly event discovery artifact from Layers 1-7 evaluation residuals. The builder searches nearby PIT event families for explanations, observation-pool candidates, and strategy-promotion review packets. It is a registered callable integration surface only: no provider calls, daemon start, model activation, broker/account mutation, destructive SQL, artifact deletion, or automatic event-family promotion.'
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
