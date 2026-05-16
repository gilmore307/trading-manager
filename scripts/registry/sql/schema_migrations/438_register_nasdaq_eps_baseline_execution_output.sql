-- Register execution-side Nasdaq EPS baseline output.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'trm_NEBE001',
    'term',
    'NASDAQ_EARNINGS_EPS_BASELINE_OUTPUT',
    'text',
    'earnings_guidance_expectation_baseline.csv',
    'trading-execution/src/trading_execution/calendar_discovery/pipeline.py',
    'nasdaq_earnings_calendar;expectation_baseline;event_risk_governor;trading_execution',
    'sync_artifact',
    'Execution-side calendar_discovery output emitted for future_pre_event_eps_consensus_snapshot tasks; contains clean pre-event Nasdaq EPS forecast baseline rows only.'
  ),
  (
    'cfg_NEBE001',
    'config',
    'NASDAQ_EPS_BASELINE_EXECUTION_ROW_ACCEPTANCE_POLICY',
    'text',
    'emit_only_when_epsForecast_present_capture_before_release_time_and_source_row_has_no_eps_or_surprise_fields',
    'trading-execution/src/trading_execution/calendar_discovery/pipeline.py',
    'nasdaq_earnings_calendar;expectation_baseline;point_in_time_policy;trading_execution',
    'sync_artifact',
    'Execution skips Nasdaq baseline rows when actual EPS or surprise fields are present, or when captured_at is not before release_time.'
  ),
  (
    'cfg_NEBE002',
    'config',
    'NASDAQ_EPS_BASELINE_EXECUTION_NON_CLAIM_POLICY',
    'text',
    'baseline_output_is_not_beat_miss_guidance_raise_cut_signed_alpha_model_activation_or_broker_mutation',
    'trading-execution/docs/05_decision.md',
    'nasdaq_earnings_calendar;expectation_baseline;signed_direction_claims;trading_execution',
    'sync_artifact',
    'Nasdaq EPS baseline output is evidence only; signed earnings/guidance claims and event-risk interventions require later reviewed comparisons and gates.'
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
