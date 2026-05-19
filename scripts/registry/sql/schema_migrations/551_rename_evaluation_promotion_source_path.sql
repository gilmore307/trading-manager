-- Align evaluation promotion-readiness source path after removing stale activation.py name.

UPDATE trading_registry
SET path = REPLACE(path, 'trading-evaluation/src/trading_evaluation/activation.py', 'trading-evaluation/src/trading_evaluation/promotion.py'),
    updated_at = NOW()
WHERE path LIKE '%trading-evaluation/src/trading_evaluation/activation.py%';
