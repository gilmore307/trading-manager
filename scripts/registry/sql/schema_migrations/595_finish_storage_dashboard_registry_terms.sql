UPDATE trading_registry
SET applies_to = replace(applies_to, 'storage/dashboard;', 'storage/dashboard_cache;'),
    updated_at = now()
WHERE applies_to LIKE '%storage/dashboard;%';

UPDATE trading_registry
SET applies_to = replace(applies_to, 'storage/dashboard,', 'storage/dashboard_cache,'),
    updated_at = now()
WHERE applies_to LIKE '%storage/dashboard,%';

UPDATE trading_registry
SET note = replace(note, 'storage/dashboard.', 'storage/dashboard_cache.'),
    updated_at = now()
WHERE note LIKE '%storage/dashboard.%';
