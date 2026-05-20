UPDATE trading_registry
SET payload = replace(payload, '/root/projects/trading-storage/storage/benchmark_datasets ', '/root/projects/trading-storage/storage/05_benchmark_datasets '),
    updated_at = now()
WHERE payload LIKE '%/root/projects/trading-storage/storage/benchmark_datasets %';

UPDATE trading_registry
SET payload = replace(payload, '/root/projects/trading-storage/storage/benchmark_datasets', '/root/projects/trading-storage/storage/05_benchmark_datasets'),
    updated_at = now()
WHERE payload LIKE '%/root/projects/trading-storage/storage/benchmark_datasets%';

UPDATE trading_registry
SET payload = replace(payload, '/root/projects/trading-storage/storage/source_data', '/root/projects/trading-storage/storage/01_source_data'),
    updated_at = now()
WHERE payload LIKE '%/root/projects/trading-storage/storage/source_data%';

UPDATE trading_registry
SET note = replace(note, 'storage/dashboard_cache.', 'storage/06_dashboard_cache.'),
    updated_at = now()
WHERE note LIKE '%storage/dashboard_cache.%';

UPDATE trading_registry
SET note = replace(note, 'storage/dashboard_cache ', 'storage/06_dashboard_cache '),
    updated_at = now()
WHERE note LIKE '%storage/dashboard_cache %';
