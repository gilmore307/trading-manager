-- Register benchmark liquidity as sampled one-shot acquisition instead of deferred full-month tick scan.

UPDATE trading_registry
SET key = 'BENCHMARK_LIQUIDITY_SAMPLED_ACQUISITION_POLICY',
    payload = 'three_five_minute_regular_session_windows_per_component_month',
    applies_to = 'benchmark_dataset_preparation;alpaca_liquidity;equity_liquidity_bar;one_shot_benchmark_acquisition',
    note = 'Primary benchmark liquidity acquisition uses three deterministic five-minute regular-session windows per equity component month: open sample, midday sample, and close sample. This prepares real trade/quote-derived liquidity evidence without full-month tick scanning or manager task/request rows.',
    updated_at = NOW()
WHERE key = 'BENCHMARK_FULL_MONTH_LIQUIDITY_DEFERRED_POLICY';

UPDATE trading_registry
SET note = 'Coverage status vocabulary for benchmark feed acquisition rows. available means a succeeded local receipt exists; deferred means the requirement is accepted but intentionally not acquired by the current route; missing means no succeeded receipt and no accepted deferral. The primary benchmark target is available=all feed acquisitions after sampled liquidity acquisition.',
    updated_at = NOW()
WHERE key = 'BENCHMARK_FEED_COVERAGE_STATUS_VALUES';
