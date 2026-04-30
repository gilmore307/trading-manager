-- Merge the unimplemented trading-manager control-plane repository into trading-main.
-- trading-main now owns request/lifecycle/promotion orchestration policy while
-- component repositories keep their runtime implementations.

UPDATE trading_registry
SET
    note = 'Canonical repository entry for the trading-main platform and control-plane repository. Owns system architecture, contracts, registry, templates, shared helpers, request/lifecycle orchestration policy, and promotion coordination; remote: https://github.com/gilmore307/trading-main.git',
    updated_at = CURRENT_TIMESTAMP
WHERE key = 'TRADING_MAIN_REPO';

DELETE FROM trading_registry
WHERE key = 'TRADING_MANAGER_REPO';

UPDATE trading_registry
SET
    applies_to = replace(applies_to, 'trading-manager', 'trading-main'),
    updated_at = CURRENT_TIMESTAMP
WHERE applies_to LIKE '%trading-manager%';

UPDATE trading_registry
SET
    note = replace(replace(replace(note,
        'trading-manager', 'trading-main control plane'),
        'manager-facing', 'control-plane-facing'),
        'manager-driven', 'control-plane-driven'),
    updated_at = CURRENT_TIMESTAMP
WHERE note LIKE '%trading-manager%'
   OR note LIKE '%manager-facing%'
   OR note LIKE '%manager-driven%';
