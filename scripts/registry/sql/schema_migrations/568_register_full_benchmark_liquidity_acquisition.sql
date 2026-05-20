-- Register benchmark liquidity as full daily regular-session acquisition.

UPDATE trading_registry
SET key = 'BENCHMARK_LIQUIDITY_FULL_DAILY_ACQUISITION_POLICY',
    payload = 'full_daily_regular_session_windows_per_component_month',
    applies_to = 'benchmark_dataset_preparation;alpaca_liquidity;equity_liquidity_bar;one_shot_benchmark_acquisition',
    note = 'Primary benchmark liquidity acquisition must use full regular-session trades/quotes over each weekday window in the equity component month, split by day to avoid whole-month timeout and memory pressure. Sampled liquidity receipts are smoke evidence only and do not satisfy benchmark coverage.',
    updated_at = NOW()
WHERE key = 'BENCHMARK_LIQUIDITY_SAMPLED_ACQUISITION_POLICY';

UPDATE trading_registry
SET note = 'Coverage status vocabulary for benchmark feed acquisition rows. available means the required full-route receipt exists; deferred means the requirement is accepted but intentionally not acquired by the current route; missing means no qualifying receipt and no accepted deferral. For Alpaca liquidity, sampled receipts do not satisfy coverage.',
    updated_at = NOW()
WHERE key = 'BENCHMARK_FEED_COVERAGE_STATUS_VALUES';
