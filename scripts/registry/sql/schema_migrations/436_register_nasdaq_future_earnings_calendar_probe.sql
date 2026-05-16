-- Register Nasdaq future earnings-calendar EPS baseline route probe.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'trm_NFEC001',
    'term',
    'NASDAQ_FUTURE_EARNINGS_CALENDAR_EPS_BASELINE_PROBE',
    'text',
    'earnings_guidance_nasdaq_future_calendar_probe_v1',
    'trading-model/storage/earnings_guidance_nasdaq_future_calendar_probe_20260518',
    'nasdaq_earnings_calendar;earnings_guidance_event_family;expectation_baseline;event_risk_governor',
    'sync_artifact',
    'Bounded future-date probe: Nasdaq returned 43 future earnings rows for 2026-05-18, including 19 EPS forecast-like rows and zero actual/surprise rows.'
  ),
  (
    'cfg_NFEC001',
    'config',
    'NASDAQ_FUTURE_EARNINGS_EPS_BASELINE_ROUTE_POLICY',
    'text',
    'future_eps_consensus_snapshot_route_requires_pre_event_capture_with_pit_clocks_and_excludes_actual_or_surprise_fields',
    'trading-model/docs/101_earnings_guidance_event_family_packet.md',
    'nasdaq_earnings_calendar;expectation_baseline;point_in_time_policy;signed_direction_claims',
    'sync_artifact',
    'Nasdaq can seed future EPS-consensus baseline snapshots only when captured before events with captured_at/as_of_time clocks; it is not accepted for post-event historical reconstruction.'
  ),
  (
    'cfg_NFEC002',
    'config',
    'NASDAQ_FUTURE_EARNINGS_BASELINE_COVERAGE_LIMIT',
    'text',
    'nasdaq_future_calendar_probe_supports_eps_forecast_not_revenue_consensus_or_guidance_expectation',
    'trading-model/docs/101_earnings_guidance_event_family_packet.md',
    'nasdaq_earnings_calendar;expectation_baseline;revenue_consensus;guidance_expectation',
    'sync_artifact',
    'The accepted future Nasdaq route is EPS-consensus candidate coverage only; revenue consensus and prior-guidance/guidance-consensus baseline routes remain separate gaps.'
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
