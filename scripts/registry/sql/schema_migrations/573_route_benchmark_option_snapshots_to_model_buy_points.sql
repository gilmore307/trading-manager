-- Route benchmark option-chain snapshots to model buy/expression points.

UPDATE trading_registry
SET payload = 'model_buy_point_triggered_chain_snapshots',
    note = 'Benchmark option-chain snapshots are generated on demand from point-in-time model buy/expression decisions during benchmark replay. They are not pre-scanned at daily open/midday/close across every benchmark component window. Specified-contract tracking and event timelines expand only after those snapshots produce concrete expiration/right/strike selections.',
    updated_at = NOW()
WHERE key = 'BENCHMARK_OPTION_CHAIN_SNAPSHOT_POLICY';

UPDATE trading_registry
SET note = 'Storage runtime CSV listing per-component one-shot feed acquisition requirements, source output roots, expected output refs, local coverage status, and feed parameters. The initial benchmark bundle includes underlying bars, full liquidity, event-layer feeds, SEC companyfacts when CIK mappings exist, and crypto candles. Option-chain snapshots are generated later from model buy/expression points, not pre-scanned in the initial acquisition plan.',
    updated_at = NOW()
WHERE key = 'BENCHMARK_FEED_ACQUISITION_PLAN';
