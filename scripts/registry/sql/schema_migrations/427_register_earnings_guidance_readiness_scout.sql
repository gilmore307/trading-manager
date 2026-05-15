-- Register earnings/guidance official-guidance readiness scout.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'scr_EGRS001',
    'script',
    'MODEL_EARNINGS_GUIDANCE_READINESS_SCOUT',
    'text',
    'PYTHONPATH=src python3 scripts/models/model_04_event_overlay/run_earnings_guidance_readiness_scout.py',
    'trading-model/scripts/models/model_04_event_overlay/run_earnings_guidance_readiness_scout.py',
    'earnings_guidance_event_family;event_family_scouting_packet_v1;event_risk_governor;model_promotion',
    'sync_artifact',
    'Deterministic local readiness audit for official guidance interpretation, expectation baselines, and signed-direction eligibility; performs no provider calls.'
  ),
  (
    'trm_EGRS001',
    'term',
    'EARNINGS_GUIDANCE_READINESS_SCOUT_Q4_2025',
    'text',
    'earnings_guidance_readiness_scout_v1',
    'trading-model/storage/earnings_guidance_readiness_scout_q4_2025_20260515',
    'earnings_guidance_event_family;event_family_scouting_packet_v1;event_risk_governor;model_promotion',
    'sync_artifact',
    'Seventh itemized earnings/guidance scout: 12 official SEC result artifacts and 11 partial result-context rows, but zero official guidance interpretations, zero expectation baselines, and zero signed-direction-ready rows.'
  ),
  (
    'cfg_EGRS001',
    'config',
    'EARNINGS_GUIDANCE_SIGNED_DIRECTION_READINESS_GATE',
    'text',
    'requires_official_guidance_interpretation_and_expectation_baseline',
    'trading-model/docs/101_earnings_guidance_event_family_packet.md',
    'earnings_guidance_event_family;model_promotion;signed_direction_claims',
    'sync_artifact',
    'Signed earnings/guidance claims remain blocked until official company guidance release/transcript interpretation and consensus or accepted expectation baselines are present point-in-time.'
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
