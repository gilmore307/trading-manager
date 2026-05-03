-- Move trading-data local storage and data-kind templates to the accepted storage/ boundary.
-- Target engine: PostgreSQL.

UPDATE trading_registry
SET payload = replace(replace(payload, 'trading-data/templates/data_kinds', 'trading-data/storage/templates/data_kinds'), 'data/storage', 'storage'),
    path = replace(replace(path, 'trading-data/templates/data_kinds', 'trading-data/storage/templates/data_kinds'), '/root/projects/trading-data/data/storage', '/root/projects/trading-data/storage'),
    applies_to = replace(replace(applies_to, 'trading-data/templates/data_kinds', 'trading-data/storage/templates/data_kinds'), 'data/storage', 'storage'),
    note = replace(replace(note, 'trading-data/templates/data_kinds', 'trading-data/storage/templates/data_kinds'), 'data/storage', 'storage')
WHERE coalesce(payload, '') LIKE '%trading-data/templates/data_kinds%'
   OR coalesce(path, '') LIKE '%trading-data/templates/data_kinds%'
   OR coalesce(applies_to, '') LIKE '%trading-data/templates/data_kinds%'
   OR coalesce(note, '') LIKE '%trading-data/templates/data_kinds%'
   OR coalesce(payload, '') LIKE '%data/storage%'
   OR coalesce(path, '') LIKE '%/root/projects/trading-data/data/storage%'
   OR coalesce(applies_to, '') LIKE '%data/storage%'
   OR coalesce(note, '') LIKE '%data/storage%';
