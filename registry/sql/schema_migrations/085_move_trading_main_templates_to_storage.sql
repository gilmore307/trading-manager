-- Move trading-main reusable templates under storage/templates.
-- Target engine: PostgreSQL.

UPDATE trading_registry
SET payload = replace(payload, 'templates/', 'storage/templates/'),
    path = replace(path, '/root/projects/trading-main/templates/', '/root/projects/trading-main/storage/templates/'),
    applies_to = replace(applies_to, 'templates/', 'storage/templates/'),
    note = replace(note, 'templates/', 'storage/templates/')
WHERE coalesce(path, '') LIKE '/root/projects/trading-main/templates/%'
   OR coalesce(payload, '') LIKE 'templates/%'
   OR coalesce(applies_to, '') LIKE '%templates/%'
   OR coalesce(note, '') LIKE '%templates/%';
