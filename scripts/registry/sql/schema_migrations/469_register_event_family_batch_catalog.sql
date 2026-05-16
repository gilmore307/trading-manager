-- Register fine-grained EventRiskGovernor event-family batch catalog entrypoint.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES (
  'scr_M8ERGFAM001',
  'script',
  'MODEL_08_EVENT_FAMILY_BATCH_CATALOG_BUILD',
  'command',
  'PYTHONPATH=src python3 scripts/models/model_08_event_risk_governor/build_event_family_batch_catalog.py',
  '/root/projects/trading-model/scripts/models/model_08_event_risk_governor/build_event_family_batch_catalog.py;/root/projects/trading-model/src/models/model_08_event_risk_governor/event_family_batch_catalog.py',
  'event_family_batch_catalog_v1;event_family_batch_summary_v1;event_family_batch_queue;event_family_scouting;model_08_event_risk_governor;fine_grained_event_family_association',
  'sync_artifact',
  'Builds the non-mutating fine-grained event-family batch catalog for Layer 8 EventRiskGovernor association scouting. Routing buckets such as symbol_news, sector_news, macro_news, sec_filing, and earnings_guidance are split into mechanism-level family queues before any price/path association study, risk promotion, or alpha claim. The helper performs no provider calls, model activation, broker/account mutation, or artifact deletion.'
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
