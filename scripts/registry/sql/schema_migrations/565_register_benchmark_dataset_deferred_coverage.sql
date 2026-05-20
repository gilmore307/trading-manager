-- Register benchmark dataset deferred coverage and OKX historical candle route.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'term_EVALBMKDS003',
    'term',
    'BENCHMARK_FEED_COVERAGE_STATUS_VALUES',
    'text',
    'available;deferred;missing',
    'trading-evaluation/src/trading_evaluation/benchmark_dataset.py',
    'benchmark_dataset_preparation;benchmark_feed_task_plan;benchmark_coverage_summary',
    'sync_artifact',
    'Coverage status vocabulary for benchmark feed task rows. available means a succeeded local receipt exists; deferred means the requirement is accepted but intentionally not dispatched by the current route; missing means no succeeded receipt and no accepted deferral.'
  ),
  (
    'term_EVALBMKDS004',
    'term',
    'BENCHMARK_FULL_MONTH_LIQUIDITY_DEFERRED_POLICY',
    'text',
    'full_month_equity_liquidity_requires_narrow_event_windows_or_dedicated_aggregate_route',
    'trading-evaluation/src/trading_evaluation/benchmark_dataset.py;trading-data/src/data_feed/02_feed_alpaca_liquidity/pipeline.py',
    'benchmark_dataset_preparation;alpaca_liquidity;equity_liquidity_bar;provider_dispatch_gate',
    'sync_artifact',
    'Primary benchmark preparation keeps monthly Alpaca liquidity task keys but marks them deferred unless a succeeded receipt already exists. The current route pulls raw trades and quotes transiently and is not the accepted way to bulk-dispatch full-month liquidity for every component.'
  ),
  (
    'term_EVALBMKDS005',
    'term',
    'OKX_HISTORICAL_BENCHMARK_CANDLE_ROUTE',
    'text',
    'okx_history_candles_for_benchmark_windows',
    'trading-data/src/data_feed/04_feed_okx_crypto_market_data/pipeline.py;trading-evaluation/src/trading_evaluation/benchmark_dataset.py',
    'benchmark_dataset_preparation;okx_crypto_market_data;crypto_spot;crypto_bar;missing_quote_order_book_context',
    'sync_artifact',
    'OKX benchmark crypto task keys use benchmark_window_start and benchmark_window_end_exclusive to fetch historical daily candles from /api/v5/market/history-candles. Historical mode persists crypto_bar rows and leaves historical trade, quote, and order-book context as accepted missing-data stress.'
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

UPDATE trading_registry
SET note = 'Storage runtime manifest describing component count, feed task count, available/deferred/missing local coverage scan counts, fail-closed task-key root, and safety flags for a benchmark dataset preparation bundle.',
    updated_at = NOW()
WHERE key = 'BENCHMARK_DATASET_PREPARATION_MANIFEST';

UPDATE trading_registry
SET note = 'Storage runtime CSV summarizing required, available, deferred, and missing local feed coverage by benchmark component and source.',
    updated_at = NOW()
WHERE key = 'BENCHMARK_COVERAGE_SUMMARY';
