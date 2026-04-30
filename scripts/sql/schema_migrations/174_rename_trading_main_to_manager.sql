-- Rename the surviving platform/control-plane repository from trading-main
-- to trading-manager after the former standalone manager repo was merged.

UPDATE trading_registry
SET
    key = 'TRADING_MANAGER_REPO',
    payload = 'trading-manager',
    path = '/root/projects/trading-manager',
    note = 'Canonical repository entry for the trading-manager platform and control-plane repository. Owns system architecture, contracts, registry, templates, shared helpers, request/lifecycle orchestration policy, and promotion coordination; remote: https://github.com/gilmore307/trading-manager.git',
    updated_at = CURRENT_TIMESTAMP
WHERE key = 'TRADING_MAIN_REPO';

UPDATE trading_registry
SET
    key = 'TRADING_MANAGER_REGISTRY',
    payload = replace(payload, 'trading-main', 'trading-manager'),
    note = replace(note, 'trading-main', 'trading-manager'),
    updated_at = CURRENT_TIMESTAMP
WHERE key = 'TRADING_MAIN_REGISTRY';

UPDATE trading_registry
SET
    payload = replace(payload, 'trading-main', 'trading-manager'),
    path = replace(path, '/root/projects/trading-main', '/root/projects/trading-manager'),
    applies_to = replace(applies_to, 'trading-main', 'trading-manager'),
    note = replace(note, 'trading-main', 'trading-manager'),
    updated_at = CURRENT_TIMESTAMP
WHERE payload LIKE '%trading-main%'
   OR path LIKE '%/root/projects/trading-main%'
   OR applies_to LIKE '%trading-main%'
   OR note LIKE '%trading-main%';
