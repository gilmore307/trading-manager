-- Register safe local all-family empirical coverage/readiness scanner.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES (
  'scr_M8ERGECS001',
  'script',
  'MODEL_08_EVENT_FAMILY_EMPIRICAL_COVERAGE_BUILD',
  'command',
  'PYTHONPATH=src python3 scripts/models/model_08_event_risk_governor/build_event_family_empirical_coverage.py',
  '/root/projects/trading-model/scripts/models/model_08_event_risk_governor/build_event_family_empirical_coverage.py;/root/projects/trading-model/src/models/model_08_event_risk_governor/event_family_empirical_coverage.py',
  'event_family_empirical_coverage_v1;event_family_empirical_coverage_summary_v1;model_08_event_risk_governor;fine_grained_event_family_association',
  'sync_artifact',
  'Builds the safe local all-family EventRiskGovernor empirical coverage/readiness scan. It uses existing local source/study artifacts only to identify families with existing empirical artifacts, candidate events needing interpretation and matched controls, missing source/parser coverage, PIT baseline blockers, residual-detector blockers, liquidity/depth blockers, and revised-definition blockers. It performs no provider calls, training, activation, broker/account mutation, destructive SQL, artifact deletion, or final alpha/risk promotion.'
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
