-- Rename storage-owned filesystem roots to semantic lifecycle names.

UPDATE trading_registry
SET payload = replace(payload, 'trading-storage/storage/benchmark/', 'trading-storage/storage/benchmark_datasets/'),
    updated_at = now()
WHERE payload LIKE '%trading-storage/storage/benchmark/%';

UPDATE trading_registry
SET path = replace(path, 'trading-storage/storage/benchmark/', 'trading-storage/storage/benchmark_datasets/'),
    updated_at = now()
WHERE path LIKE '%trading-storage/storage/benchmark/%';

UPDATE trading_registry
SET payload = replace(payload, 'trading-storage/storage/data/', 'trading-storage/storage/source_data/'),
    updated_at = now()
WHERE payload LIKE '%trading-storage/storage/data/%';

UPDATE trading_registry
SET path = replace(path, 'trading-storage/storage/data/', 'trading-storage/storage/source_data/'),
    updated_at = now()
WHERE path LIKE '%trading-storage/storage/data/%';

UPDATE trading_registry
SET payload = replace(payload, 'trading-storage/storage/manager/', 'trading-storage/storage/control_plane/'),
    updated_at = now()
WHERE payload LIKE '%trading-storage/storage/manager/%';

UPDATE trading_registry
SET path = replace(path, 'trading-storage/storage/manager/', 'trading-storage/storage/control_plane/'),
    updated_at = now()
WHERE path LIKE '%trading-storage/storage/manager/%';

UPDATE trading_registry
SET payload = replace(payload, 'trading-storage/storage/model/', 'trading-storage/storage/model_artifacts/'),
    updated_at = now()
WHERE payload LIKE '%trading-storage/storage/model/%';

UPDATE trading_registry
SET path = replace(path, 'trading-storage/storage/model/', 'trading-storage/storage/model_artifacts/'),
    updated_at = now()
WHERE path LIKE '%trading-storage/storage/model/%';

UPDATE trading_registry
SET payload = replace(payload, 'trading-storage/storage/execution/', 'trading-storage/storage/execution_artifacts/'),
    updated_at = now()
WHERE payload LIKE '%trading-storage/storage/execution/%';

UPDATE trading_registry
SET path = replace(path, 'trading-storage/storage/execution/', 'trading-storage/storage/execution_artifacts/'),
    updated_at = now()
WHERE path LIKE '%trading-storage/storage/execution/%';

UPDATE trading_registry
SET payload = replace(payload, 'storage/dashboard/', 'storage/dashboard_cache/'),
    updated_at = now()
WHERE payload LIKE '%storage/dashboard/%';

UPDATE trading_registry
SET path = replace(path, 'storage/dashboard/', 'storage/dashboard_cache/'),
    updated_at = now()
WHERE path LIKE '%storage/dashboard/%';

UPDATE trading_registry
SET payload = replace(payload, '/root/projects/trading-storage/storage/benchmark ', '/root/projects/trading-storage/storage/benchmark_datasets '),
    updated_at = now()
WHERE payload LIKE '%/root/projects/trading-storage/storage/benchmark %';

UPDATE trading_registry
SET payload = replace(payload, '/root/projects/trading-storage/storage/benchmark$', '/root/projects/trading-storage/storage/benchmark_datasets'),
    updated_at = now()
WHERE payload LIKE '%/root/projects/trading-storage/storage/benchmark$%';

UPDATE trading_registry
SET payload = replace(payload, '--output-root /root/projects/trading-storage/storage/benchmark ', '--output-root /root/projects/trading-storage/storage/benchmark_datasets '),
    updated_at = now()
WHERE payload LIKE '%--output-root /root/projects/trading-storage/storage/benchmark %';

UPDATE trading_registry
SET payload = replace(payload, '--data-root /root/projects/trading-storage/storage/data', '--data-root /root/projects/trading-storage/storage/source_data'),
    updated_at = now()
WHERE payload LIKE '%--data-root /root/projects/trading-storage/storage/data%';

UPDATE trading_registry
SET payload = replace(payload, 'storage/dashboard;', 'storage/dashboard_cache;'),
    updated_at = now()
WHERE payload LIKE '%storage/dashboard;%';

UPDATE trading_registry
SET payload = replace(payload, 'storage/dashboard,', 'storage/dashboard_cache,'),
    updated_at = now()
WHERE payload LIKE '%storage/dashboard,%';

UPDATE trading_registry
SET note = replace(note, 'storage/dashboard/', 'storage/dashboard_cache/'),
    updated_at = now()
WHERE note LIKE '%storage/dashboard/%';

UPDATE trading_registry
SET note = replace(note, 'storage/dashboard ', 'storage/dashboard_cache '),
    updated_at = now()
WHERE note LIKE '%storage/dashboard %';

