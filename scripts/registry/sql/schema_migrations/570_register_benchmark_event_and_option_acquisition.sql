-- Register benchmark event-layer and option-chain acquisition requirements.

UPDATE trading_registry
SET note = 'Storage runtime CSV listing per-component one-shot feed acquisition requirements, source output roots, expected output refs, local coverage status, and feed parameters. The benchmark bundle includes underlying bars, full liquidity, event-layer feeds, SEC companyfacts when CIK mappings exist, crypto candles, and option-chain selection snapshots. This is not a manager task plan and does not create reusable task keys.',
    updated_at = NOW()
WHERE key = 'BENCHMARK_FEED_ACQUISITION_PLAN';

UPDATE trading_registry
SET note = 'Storage runtime manifest describing component count, feed acquisition count, available/deferred/missing local coverage scan counts, acquisition-plan ref, and safety flags for a benchmark dataset preparation bundle. It records manager_request_route_used=false because benchmark data acquisition is a sealed one-shot action rather than a manager task route. Initial option-chain snapshots are included; specified-contract ThetaData tracking and event timelines expand after concrete contract selection.',
    updated_at = NOW()
WHERE key = 'BENCHMARK_DATASET_PREPARATION_MANIFEST';

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'term_EVALBMKDS005',
    'term',
    'BENCHMARK_EVENT_LAYER_ACQUISITION_FEEDS',
    'text',
    '03_feed_alpaca_news;05_feed_gdelt_news;07_feed_trading_economics_calendar_web;08_feed_sec_company_financials',
    'trading-evaluation/docs/22_benchmark_dataset_preparation.md',
    'benchmark_dataset_preparation;event_layer;source_09_event_risk_governor;one_shot_benchmark_acquisition',
    'sync_artifact',
    'Event-layer benchmark acquisition requires symbol-scoped Alpaca news, broad GDELT news, high-importance U.S. Trading Economics calendar rows, and mapped SEC companyfacts for single-name equities.'
  ),
  (
    'term_EVALBMKDS006',
    'term',
    'BENCHMARK_OPTION_CHAIN_SNAPSHOT_POLICY',
    'text',
    'daily_open_midday_close_chain_snapshots',
    'trading-evaluation/docs/22_benchmark_dataset_preparation.md',
    'benchmark_dataset_preparation;thetadata_option_selection_snapshot;option_layer;one_shot_benchmark_acquisition',
    'sync_artifact',
    'Benchmark option-layer preparation includes daily open, midday, and close ThetaData option-chain selection snapshots for equity and ETF components. Specified-contract tracking and event timelines are generated only after those snapshots produce concrete expiration/right/strike selections.'
  )
ON CONFLICT (id) DO UPDATE
SET payload = EXCLUDED.payload,
    key = EXCLUDED.key,
    kind = EXCLUDED.kind,
    payload_format = EXCLUDED.payload_format,
    path = EXCLUDED.path,
    applies_to = EXCLUDED.applies_to,
    artifact_sync_policy = EXCLUDED.artifact_sync_policy,
    note = EXCLUDED.note,
    updated_at = NOW();
