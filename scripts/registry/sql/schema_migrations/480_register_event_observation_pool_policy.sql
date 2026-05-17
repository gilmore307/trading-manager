-- Register EventRiskGovernor observation-pool and promotion policy builder.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES (
  'scr_M8ERGOP001',
  'script',
  'MODEL_08_EVENT_OBSERVATION_POOL_POLICY_BUILD',
  'command',
  'PYTHONPATH=src python3 scripts/models/model_08_event_risk_governor/build_event_observation_pool_policy.py',
  '/root/projects/trading-model/scripts/models/model_08_event_risk_governor/build_event_observation_pool_policy.py;/root/projects/trading-model/src/models/model_08_event_risk_governor/event_observation_pool_policy.py',
  'event_observation_pool_policy_v1;event_observation_pool_policy_summary_v1;model_08_event_risk_governor;event_observation_pool;event_strategy_promotion_review',
  'sync_artifact',
  'Builds the EventRiskGovernor event observation-pool and promotion policy artifact. It separates historical all-event residual-anomaly research from realtime observation-pool monitoring, and requires script-emitted evidence plus agent review before any event family is promoted from correction overlay to strategy-decision scope.'
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
