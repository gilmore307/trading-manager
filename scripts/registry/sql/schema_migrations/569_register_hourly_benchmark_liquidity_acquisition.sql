-- Narrow benchmark liquidity full-route windows from day to hour.

UPDATE trading_registry
SET key = 'BENCHMARK_LIQUIDITY_FULL_HOURLY_ACQUISITION_POLICY',
    payload = 'full_hourly_regular_session_windows_per_component_month',
    note = 'Primary benchmark liquidity acquisition must use full regular-session trades/quotes over hourly windows across the equity component month. Smaller windows keep raw trade/quote memory bounded while preserving full time coverage. Sampled liquidity receipts are smoke evidence only and do not satisfy benchmark coverage.',
    updated_at = NOW()
WHERE key = 'BENCHMARK_LIQUIDITY_FULL_DAILY_ACQUISITION_POLICY';
