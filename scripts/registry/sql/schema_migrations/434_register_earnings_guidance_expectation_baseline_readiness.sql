-- Register earnings/guidance expectation baseline readiness gate.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'scr_EGEB001',
    'script',
    'MODEL_EARNINGS_GUIDANCE_EXPECTATION_BASELINE_READINESS',
    'text',
    'PYTHONPATH=src python3 scripts/models/model_04_event_overlay/run_earnings_guidance_expectation_baseline_readiness.py',
    'trading-model/scripts/models/model_04_event_overlay/run_earnings_guidance_expectation_baseline_readiness.py',
    'earnings_guidance_event_family;event_family_scouting_packet_v1;event_risk_governor;model_promotion',
    'sync_artifact',
    'Deterministic local readiness gate that validates point-in-time expectation baseline artifacts before any signed earnings/guidance claim; performs no provider calls.'
  ),
  (
    'trm_EGEB001',
    'term',
    'EARNINGS_GUIDANCE_EXPECTATION_BASELINE_READINESS_Q4_2025',
    'text',
    'earnings_guidance_expectation_baseline_readiness_v1',
    'trading-model/storage/earnings_guidance_expectation_baseline_readiness_q4_2025_20260515',
    'earnings_guidance_event_family;event_family_scouting_packet_v1;event_risk_governor;model_promotion',
    'sync_artifact',
    'Twelfth itemized earnings/guidance scout: 12 events, zero supplied baseline artifacts, 12 missing point-in-time expectation baselines, and zero signed-direction-ready rows.'
  ),
  (
    'cfg_EGEB001',
    'config',
    'EARNINGS_GUIDANCE_EXPECTATION_BASELINE_ACCEPTED_TYPES',
    'json',
    '["eps_consensus","revenue_consensus","prior_company_guidance","guidance_consensus_or_analyst_range"]',
    'trading-model/docs/101_earnings_guidance_event_family_packet.md',
    'earnings_guidance_event_family;expectation_baseline;signed_direction_claims;event_risk_governor',
    'sync_artifact',
    'Accepted point-in-time baseline artifact types for earnings/guidance signed-claim readiness.'
  ),
  (
    'cfg_EGEB002',
    'config',
    'EARNINGS_GUIDANCE_EXPECTATION_BASELINE_PIT_CLOCK_POLICY',
    'text',
    'baseline_requires_source_ref_captured_at_as_of_time_and_predates_date_only_event_clock',
    'trading-model/docs/101_earnings_guidance_event_family_packet.md',
    'earnings_guidance_event_family;expectation_baseline;point_in_time_policy;signed_direction_claims',
    'sync_artifact',
    'Baseline artifacts must preserve provenance and point-in-time clocks; with date-only event clocks, same-day baselines are not accepted until timestamped release clocks exist.'
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
