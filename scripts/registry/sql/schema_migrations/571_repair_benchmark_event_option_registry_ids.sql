-- Repair benchmark dataset preparation term ids after adding event/option terms.

DELETE FROM trading_registry
WHERE key IN (
    'OKX_HISTORICAL_BENCHMARK_CANDLE_ROUTE',
    'BENCHMARK_EVENT_LAYER_ACQUISITION_FEEDS',
    'BENCHMARK_OPTION_CHAIN_SNAPSHOT_POLICY'
);

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'term_EVALBMKDS005',
    'term',
    'OKX_HISTORICAL_BENCHMARK_CANDLE_ROUTE',
    'text',
    'okx_history_candles_for_benchmark_windows',
    'trading-data/src/data_feed/04_feed_okx_crypto_market_data/pipeline.py',
    'benchmark_dataset_preparation;okx_crypto_market_data;one_shot_benchmark_acquisition',
    'sync_artifact',
    'Benchmark crypto daily candles use the OKX historical candles endpoint for explicit benchmark windows. Quote/order-book context remains an accepted missing-data stress, not a hidden requirement.'
  ),
  (
    'term_EVALBMKDS006',
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
    'term_EVALBMKDS007',
    'term',
    'BENCHMARK_OPTION_CHAIN_SNAPSHOT_POLICY',
    'text',
    'daily_open_midday_close_chain_snapshots',
    'trading-evaluation/docs/22_benchmark_dataset_preparation.md',
    'benchmark_dataset_preparation;thetadata_option_selection_snapshot;option_layer;one_shot_benchmark_acquisition',
    'sync_artifact',
    'Benchmark option-layer preparation includes daily open, midday, and close ThetaData option-chain selection snapshots for equity and ETF components. Specified-contract tracking and event timelines are generated only after those snapshots produce concrete expiration/right/strike selections.'
  );
