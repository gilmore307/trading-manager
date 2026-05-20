UPDATE trading_registry
SET payload = replace(payload, 'storage/dashboard;', 'storage/dashboard_cache;'),
    updated_at = now()
WHERE payload LIKE '%storage/dashboard;%';

UPDATE trading_registry
SET payload = replace(payload, 'storage/dashboard,', 'storage/dashboard_cache,'),
    updated_at = now()
WHERE payload LIKE '%storage/dashboard,%';

UPDATE trading_registry
SET note = replace(note, 'storage/dashboard ', 'storage/dashboard_cache '),
    updated_at = now()
WHERE note LIKE '%storage/dashboard %';

UPDATE trading_registry
SET note = replace(note, 'storage/dashboard/', 'storage/dashboard_cache/'),
    updated_at = now()
WHERE note LIKE '%storage/dashboard/%';

UPDATE trading_registry
SET note = replace(note, 'storage/archive/', 'storage/lifecycle/archive/'),
    updated_at = now()
WHERE note LIKE '%storage/archive/%';

UPDATE trading_registry
SET note = replace(note, 'storage/tmp, storage/cache, storage/staging, storage/logs, storage/runs, storage/outputs', 'storage/lifecycle/tmp, storage/lifecycle/cache, storage/lifecycle/staging, storage/lifecycle/logs, storage/lifecycle/runs, storage/lifecycle/outputs'),
    updated_at = now()
WHERE note LIKE '%storage/tmp, storage/cache, storage/staging, storage/logs, storage/runs, storage/outputs%';
