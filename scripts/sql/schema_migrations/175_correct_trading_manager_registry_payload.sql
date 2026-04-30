-- Correct title-case payload text left by the lowercase trading-main rename.

UPDATE trading_registry
SET
    payload = replace(payload, 'Trading-main', 'Trading-manager'),
    note = replace(note, 'Trading-main', 'Trading-manager'),
    updated_at = CURRENT_TIMESTAMP
WHERE key = 'TRADING_MANAGER_REGISTRY'
   OR payload LIKE '%Trading-main%'
   OR note LIKE '%Trading-main%';
