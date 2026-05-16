-- Register earnings/guidance baseline source audit.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'scr_EGBS001',
    'script',
    'MODEL_EARNINGS_GUIDANCE_BASELINE_SOURCE_AUDIT',
    'text',
    'PYTHONPATH=src python3 scripts/models/model_04_event_overlay/run_earnings_guidance_baseline_source_audit.py',
    'trading-model/scripts/models/model_04_event_overlay/run_earnings_guidance_baseline_source_audit.py',
    'earnings_guidance_event_family;expectation_baseline;event_risk_governor;model_promotion',
    'sync_artifact',
    'Deterministic local audit of already captured calendar artifacts as point-in-time expectation baseline candidates; performs no provider calls.'
  ),
  (
    'trm_EGBS001',
    'term',
    'EARNINGS_GUIDANCE_BASELINE_SOURCE_AUDIT_Q4_2025',
    'text',
    'earnings_guidance_baseline_source_audit_v1',
    'trading-model/storage/earnings_guidance_baseline_source_audit_q4_2025_20260515',
    'earnings_guidance_event_family;expectation_baseline;event_risk_governor;model_promotion',
    'sync_artifact',
    'Thirteenth itemized earnings/guidance scout: 12 matched Nasdaq calendar rows, 12 EPS forecast-like fields, zero PIT-accepted baseline rows, zero revenue forecast rows, and zero signed-direction-ready rows.'
  ),
  (
    'cfg_EGBS001',
    'config',
    'NASDAQ_EARNINGS_CALENDAR_PIT_BASELINE_POLICY',
    'text',
    'future_eps_consensus_route_requires_clean_pre_event_snapshot_and_must_not_use_post_event_actual_or_surprise_fields',
    'trading-model/docs/101_earnings_guidance_event_family_packet.md',
    'nasdaq_earnings_calendar;expectation_baseline;point_in_time_policy;signed_direction_claims',
    'sync_artifact',
    'Nasdaq earnings-calendar EPS forecast fields may be future baseline candidates only when captured before the event with PIT clocks; historical post-event snapshots containing actual/surprise fields are rejected.'
  ),
  (
    'cfg_EGBS002',
    'config',
    'EARNINGS_GUIDANCE_BASELINE_REVENUE_AND_GUIDANCE_ROUTE_GAP',
    'text',
    'existing_nasdaq_calendar_audit_found_zero_revenue_consensus_or_guidance_expectation_baselines',
    'trading-model/docs/101_earnings_guidance_event_family_packet.md',
    'earnings_guidance_event_family;expectation_baseline;revenue_consensus;guidance_expectation',
    'sync_artifact',
    'Existing audited calendar artifacts do not provide revenue consensus or prior-guidance/guidance-consensus baselines; separate source routes remain required.'
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
