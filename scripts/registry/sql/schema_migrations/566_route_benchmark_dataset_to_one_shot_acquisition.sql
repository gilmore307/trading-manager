-- Route benchmark dataset preparation away from reusable manager task keys.

UPDATE trading_registry
SET note = 'Prepare storage-owned benchmark dataset manifests and one-shot feed acquisition requirements from a benchmark contract. The script scans local trading-data coverage but performs no provider calls, manager task/request creation, SQL mutation, benchmark freeze, model training, activation, broker execution, or account mutation.',
    updated_at = NOW()
WHERE key = 'TRADING_EVALUATION_PREPARE_BENCHMARK_DATASET';

UPDATE trading_registry
SET note = 'Storage runtime manifest describing component count, feed acquisition count, available/deferred/missing local coverage scan counts, acquisition-plan ref, and safety flags for a benchmark dataset preparation bundle. It records manager_request_route_used=false because benchmark data acquisition is a sealed one-shot action rather than a manager task route.',
    updated_at = NOW()
WHERE key = 'BENCHMARK_DATASET_PREPARATION_MANIFEST';

UPDATE trading_registry
SET key = 'BENCHMARK_FEED_ACQUISITION_PLAN',
    payload = 'benchmark_feed_acquisition_plan',
    path = 'trading-storage/storage/benchmark/<contract_id>/feed_acquisition_plan.csv',
    applies_to = 'trading-storage;trading-evaluation;trading-data;benchmark_dataset_preparation;one_shot_benchmark_acquisition',
    note = 'Storage runtime CSV listing per-component one-shot feed acquisition requirements, source output roots, expected output refs, local coverage status, and feed parameters. This is not a manager task plan and does not create reusable task keys.',
    updated_at = NOW()
WHERE key = 'BENCHMARK_FEED_TASK_PLAN';

UPDATE trading_registry
SET payload = 'prepared_one_shot_acquisition_bundle',
    applies_to = 'benchmark_dataset_preparation;one_shot_benchmark_acquisition;benchmark_freeze_gate',
    note = 'Status meaning the benchmark dataset artifacts and one-shot acquisition requirements have been prepared, but live provider calls, benchmark freeze, SQL mutation, model training, and activation have not occurred. The benchmark dataset route does not create manager task/request rows.',
    updated_at = NOW()
WHERE key = 'BENCHMARK_DATASET_PREPARATION_STATUS';

UPDATE trading_registry
SET key = 'BENCHMARK_ONE_SHOT_ACQUISITION_GATE_POLICY',
    payload = 'benchmark_acquisition_requires_one_shot_provider_gate_no_manager_task_route',
    applies_to = 'benchmark_dataset_preparation;one_shot_benchmark_acquisition;trading-data',
    note = 'Benchmark dataset acquisition is a sealed one-time action. Preparation emits feed acquisition requirements and local coverage scans only; live provider calls require a separate one-shot gate and must not be represented as reusable manager task keys.',
    updated_at = NOW()
WHERE key = 'BENCHMARK_PROVIDER_TASK_KEYS_FAIL_CLOSED_POLICY';

UPDATE trading_registry
SET applies_to = 'benchmark_dataset_preparation;benchmark_feed_acquisition_plan;benchmark_coverage_summary',
    note = 'Coverage status vocabulary for benchmark feed acquisition rows. available means a succeeded local receipt exists; deferred means the requirement is accepted but intentionally not acquired by the current route; missing means no succeeded receipt and no accepted deferral.',
    updated_at = NOW()
WHERE key = 'BENCHMARK_FEED_COVERAGE_STATUS_VALUES';

UPDATE trading_registry
SET applies_to = 'benchmark_dataset_preparation;alpaca_liquidity;equity_liquidity_bar;one_shot_benchmark_acquisition',
    note = 'Primary benchmark preparation keeps monthly Alpaca liquidity acquisition requirements but marks them deferred unless a succeeded receipt already exists. The current route pulls raw trades and quotes transiently and is not the accepted way to acquire full-month liquidity for every benchmark component.',
    updated_at = NOW()
WHERE key = 'BENCHMARK_FULL_MONTH_LIQUIDITY_DEFERRED_POLICY';

UPDATE trading_registry
SET note = 'OKX benchmark crypto acquisition rows use benchmark_window_start and benchmark_window_end_exclusive to fetch historical daily candles from /api/v5/market/history-candles. Historical mode persists crypto_bar rows and leaves historical trade, quote, and order-book context as accepted missing-data stress.',
    updated_at = NOW()
WHERE key = 'OKX_HISTORICAL_BENCHMARK_CANDLE_ROUTE';
