-- Prefix storage-owned semantic roots with process-order numbers.

UPDATE trading_registry
SET payload = replace(payload, 'trading-storage/storage/source_data/', 'trading-storage/storage/01_source_data/'),
    updated_at = now()
WHERE payload LIKE '%trading-storage/storage/source_data/%';

UPDATE trading_registry
SET path = replace(path, 'trading-storage/storage/source_data/', 'trading-storage/storage/01_source_data/'),
    updated_at = now()
WHERE path LIKE '%trading-storage/storage/source_data/%';

UPDATE trading_registry
SET payload = replace(payload, 'trading-storage/storage/control_plane/', 'trading-storage/storage/02_control_plane/'),
    updated_at = now()
WHERE payload LIKE '%trading-storage/storage/control_plane/%';

UPDATE trading_registry
SET path = replace(path, 'trading-storage/storage/control_plane/', 'trading-storage/storage/02_control_plane/'),
    updated_at = now()
WHERE path LIKE '%trading-storage/storage/control_plane/%';

UPDATE trading_registry
SET payload = replace(payload, 'trading-storage/storage/model_artifacts/', 'trading-storage/storage/03_model_artifacts/'),
    updated_at = now()
WHERE payload LIKE '%trading-storage/storage/model_artifacts/%';

UPDATE trading_registry
SET path = replace(path, 'trading-storage/storage/model_artifacts/', 'trading-storage/storage/03_model_artifacts/'),
    updated_at = now()
WHERE path LIKE '%trading-storage/storage/model_artifacts/%';

UPDATE trading_registry
SET payload = replace(payload, 'trading-storage/storage/execution_artifacts/', 'trading-storage/storage/04_execution_artifacts/'),
    updated_at = now()
WHERE payload LIKE '%trading-storage/storage/execution_artifacts/%';

UPDATE trading_registry
SET path = replace(path, 'trading-storage/storage/execution_artifacts/', 'trading-storage/storage/04_execution_artifacts/'),
    updated_at = now()
WHERE path LIKE '%trading-storage/storage/execution_artifacts/%';

UPDATE trading_registry
SET payload = replace(payload, 'trading-storage/storage/benchmark_datasets/', 'trading-storage/storage/05_benchmark_datasets/'),
    updated_at = now()
WHERE payload LIKE '%trading-storage/storage/benchmark_datasets/%';

UPDATE trading_registry
SET path = replace(path, 'trading-storage/storage/benchmark_datasets/', 'trading-storage/storage/05_benchmark_datasets/'),
    updated_at = now()
WHERE path LIKE '%trading-storage/storage/benchmark_datasets/%';

UPDATE trading_registry
SET payload = replace(payload, 'storage/dashboard_cache/', 'storage/06_dashboard_cache/'),
    updated_at = now()
WHERE payload LIKE '%storage/dashboard_cache/%';

UPDATE trading_registry
SET path = replace(path, 'storage/dashboard_cache/', 'storage/06_dashboard_cache/'),
    updated_at = now()
WHERE path LIKE '%storage/dashboard_cache/%';

UPDATE trading_registry
SET applies_to = replace(applies_to, 'storage/dashboard_cache', 'storage/06_dashboard_cache'),
    updated_at = now()
WHERE applies_to LIKE '%storage/dashboard_cache%';

UPDATE trading_registry
SET note = replace(note, 'storage/dashboard_cache/', 'storage/06_dashboard_cache/'),
    updated_at = now()
WHERE note LIKE '%storage/dashboard_cache/%';

UPDATE trading_registry
SET note = replace(note, 'storage/dashboard_cache ', 'storage/06_dashboard_cache '),
    updated_at = now()
WHERE note LIKE '%storage/dashboard_cache %';

UPDATE trading_registry
SET note = replace(note, 'storage/lifecycle/', 'storage/90_lifecycle/'),
    updated_at = now()
WHERE note LIKE '%storage/lifecycle/%';

UPDATE trading_registry
SET payload = replace(payload, 'storage/lifecycle/', 'storage/90_lifecycle/'),
    updated_at = now()
WHERE payload LIKE '%storage/lifecycle/%';

UPDATE trading_registry
SET path = replace(path, 'storage/lifecycle/', 'storage/90_lifecycle/'),
    updated_at = now()
WHERE path LIKE '%storage/lifecycle/%';

UPDATE trading_registry
SET note = replace(note, 'storage/lifecycle/tmp, storage/lifecycle/cache, storage/lifecycle/staging, storage/lifecycle/logs, storage/lifecycle/runs, storage/lifecycle/outputs', 'storage/90_lifecycle/tmp, storage/90_lifecycle/cache, storage/90_lifecycle/staging, storage/90_lifecycle/logs, storage/90_lifecycle/runs, storage/90_lifecycle/outputs'),
    updated_at = now()
WHERE note LIKE '%storage/lifecycle/tmp, storage/lifecycle/cache, storage/lifecycle/staging, storage/lifecycle/logs, storage/lifecycle/runs, storage/lifecycle/outputs%';
