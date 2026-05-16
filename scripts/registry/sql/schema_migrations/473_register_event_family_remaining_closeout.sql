-- Register safe local remaining event-family closeout entrypoint.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES (
  'scr_M8ERGREM001',
  'script',
  'MODEL_08_EVENT_FAMILY_REMAINING_CLOSEOUT_BUILD',
  'command',
  'PYTHONPATH=src python3 scripts/models/model_08_event_risk_governor/build_event_family_remaining_closeout.py',
  '/root/projects/trading-model/scripts/models/model_08_event_risk_governor/build_event_family_remaining_closeout.py;/root/projects/trading-model/src/models/model_08_event_risk_governor/event_family_remaining_closeout.py',
  'event_family_remaining_closeout_v1;event_family_remaining_closeout_summary_v1;model_08_event_risk_governor;fine_grained_event_family_association',
  'sync_artifact',
  'Builds the safe local remaining event-family closeout artifact. It accounts for all 29 fine-grained families, separates risk/control candidates from packet/baseline/residual/liquidity blockers, defers the current option-abnormality definition as low-signal, and promotes no standalone directional alpha. It performs no provider calls, model activation, broker/account mutation, or artifact deletion.'
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
