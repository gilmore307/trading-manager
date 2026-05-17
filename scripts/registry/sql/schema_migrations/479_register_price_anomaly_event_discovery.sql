-- Register reverse price-anomaly/event-family discovery builder.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES (
  'scr_M8ERGPA001',
  'script',
  'MODEL_08_PRICE_ANOMALY_EVENT_DISCOVERY_BUILD',
  'command',
  'PYTHONPATH=src python3 scripts/models/model_08_event_risk_governor/build_price_anomaly_event_discovery.py',
  '/root/projects/trading-model/scripts/models/model_08_event_risk_governor/build_price_anomaly_event_discovery.py;/root/projects/trading-model/src/models/model_08_event_risk_governor/price_anomaly_event_discovery.py',
  'price_anomaly_event_discovery_v1;price_anomaly_event_discovery_summary_v1;model_08_event_risk_governor;reverse_event_family_discovery',
  'sync_artifact',
  'Builds the reverse price-anomaly/event-family discovery artifact. It starts from local price anomalies, scans nearby event-family mentions for enrichment/commonality, and performs no provider calls, model training, activation, broker/account mutation, destructive SQL, or artifact deletion.'
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
