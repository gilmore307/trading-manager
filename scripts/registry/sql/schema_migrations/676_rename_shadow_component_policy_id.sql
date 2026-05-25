-- Align the Shadow runtime component policy row id with C08 numbering.

UPDATE trading_registry
SET id = 'cfg_SHADOWC08001',
    updated_at = NOW()
WHERE id = 'cfg_SHADOWS01001';
