-- Register Layer 2 stage coverage and preflight accepted-skip policy.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'cfg_L2SCOV001',
    'config',
    'LAYER_TWO_STAGE_COVERAGE_GATE',
    'text',
    'layer_02_sector_context.data_acquisition uses manager_stage_coverage_v1 over the reviewed 25-symbol Layer 2 ETF universe; Layer 1 and Layer 2 Alpaca-bar rows must be matched by request id/universe, not by month alone.',
    'trading-manager/src/trading_manager_tasks/stage_coverage.py',
    'layer_02_sector_context.data_acquisition;manager_stage_coverage_v1;failure_register;01_feed_alpaca_bars',
    'sync_artifact',
    'Stage coverage supports Layer 2 sector-context acquisition and avoids mixing Layer 1 and Layer 2 Alpaca-bar rows for the same month.'
  ),
  (
    'cfg_PFSKIP001',
    'config',
    'PREFLIGHT_ACCEPTED_SKIP_POLICY',
    'text',
    'A reviewed not-yet-listed request may be recorded as accepted_skip with skip_future_matching=true before a known-useless provider call; stage coverage counts it as a reviewed terminal skip, not as ready, and downstream remains blocked until ready plus reviewed skips cover the expected stage count.',
    'trading-manager/src/trading_manager_tasks/stage_coverage.py',
    'manager_failure_register_v1;manager_stage_coverage_v1;accepted_skip;no_data_not_yet_listed',
    'sync_artifact',
    'Preflight accepted skips reduce known-useless provider calls while preserving the fact that no provider output exists. They require agent_review_ref and do not authorize provider dispatch.'
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
