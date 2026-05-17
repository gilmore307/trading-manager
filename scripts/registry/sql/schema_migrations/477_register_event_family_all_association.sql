-- Register all-family local event/price association measurement builder.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES (
  'scr_M8ERGAA001',
  'script',
  'MODEL_08_EVENT_FAMILY_ALL_ASSOCIATION_BUILD',
  'command',
  'PYTHONPATH=src python3 scripts/models/model_08_event_risk_governor/build_event_family_all_association.py',
  '/root/projects/trading-model/scripts/models/model_08_event_risk_governor/build_event_family_all_association.py;/root/projects/trading-model/src/models/model_08_event_risk_governor/event_family_all_association.py',
  'event_family_all_association_v1;event_family_all_association_summary_v1;model_08_event_risk_governor;event_family_price_association',
  'sync_artifact',
  'Builds the local all-family event/price association measurement. It emits all 29 event-family rows, separates accepted prior risk/control associations from local keyword/proxy screening associations, no-local-label data gaps, and required-precondition blockers, and performs no provider calls, model training, activation, broker/account mutation, destructive SQL, or artifact deletion.'
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
