-- Use a term-prefixed registry id for the selected-target blocker token.

UPDATE trading_registry
SET id = 'term_DU002',
    updated_at = NOW()
WHERE id = 'sts_DU001';
