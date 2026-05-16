-- Register safe local event-price association readiness batch entrypoint.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES (
  'scr_M8ERGPAR001',
  'script',
  'MODEL_08_EVENT_PRICE_ASSOCIATION_READINESS_BUILD',
  'command',
  'PYTHONPATH=src python3 scripts/models/model_08_event_risk_governor/build_event_price_association_readiness.py',
  '/root/projects/trading-model/scripts/models/model_08_event_risk_governor/build_event_price_association_readiness.py;/root/projects/trading-model/src/models/model_08_event_risk_governor/event_price_association_readiness.py',
  'event_price_association_readiness_batch_v1;event_price_association_family_readiness;event_price_association_candidate_events;event_price_association_price_labels;model_08_event_risk_governor;fine_grained_event_family_association',
  'sync_artifact',
  'Builds the safe local first event-price association readiness slice for selected high-priority EventRiskGovernor families. It inventories existing local artifacts, emits candidate-event/readiness/price-label diagnostics where possible, keeps underpowered or unstandardized families blocked, and performs no provider calls, model activation, broker/account mutation, or artifact deletion.'
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
