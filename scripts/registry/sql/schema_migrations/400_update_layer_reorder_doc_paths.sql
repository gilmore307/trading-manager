-- Update current registry doc paths for the conceptual Layer 4-8 reorder.
-- Legacy physical package/script/table names are intentionally preserved until a dedicated implementation migration.

UPDATE trading_registry
SET path = REPLACE(path, 'trading-model/docs/05_layer_04_event_overlay.md', 'trading-model/docs/09_layer_08_event_risk_governor.md'),
    updated_at = NOW()
WHERE path LIKE '%trading-model/docs/05_layer_04_event_overlay.md%';

UPDATE trading_registry
SET path = REPLACE(path, 'trading-model/docs/06_layer_05_alpha_confidence.md', 'trading-model/docs/05_layer_04_alpha_confidence.md'),
    updated_at = NOW()
WHERE path LIKE '%trading-model/docs/06_layer_05_alpha_confidence.md%';

UPDATE trading_registry
SET path = REPLACE(path, 'trading-model/docs/07_layer_06_position_projection.md', 'trading-model/docs/06_layer_05_position_projection.md'),
    updated_at = NOW()
WHERE path LIKE '%trading-model/docs/07_layer_06_position_projection.md%';

UPDATE trading_registry
SET path = REPLACE(path, 'trading-model/docs/08_layer_07_underlying_action.md', 'trading-model/docs/07_layer_06_underlying_action.md'),
    updated_at = NOW()
WHERE path LIKE '%trading-model/docs/08_layer_07_underlying_action.md%';

UPDATE trading_registry
SET path = REPLACE(path, 'trading-model/docs/09_layer_08_option_expression.md', 'trading-model/docs/08_layer_07_trading_guidance.md'),
    updated_at = NOW()
WHERE path LIKE '%trading-model/docs/09_layer_08_option_expression.md%';

UPDATE trading_registry
SET path = REPLACE(path, 'trading-data/docs/05_layer_04_event_overlay.md', 'trading-data/docs/09_layer_08_event_risk_governor.md'),
    updated_at = NOW()
WHERE path LIKE '%trading-data/docs/05_layer_04_event_overlay.md%';

UPDATE trading_registry
SET path = REPLACE(path, 'trading-data/docs/06_layer_05_alpha_confidence.md', 'trading-data/docs/05_layer_04_alpha_confidence.md'),
    updated_at = NOW()
WHERE path LIKE '%trading-data/docs/06_layer_05_alpha_confidence.md%';

UPDATE trading_registry
SET path = REPLACE(path, 'trading-data/docs/07_layer_06_position_projection.md', 'trading-data/docs/06_layer_05_position_projection.md'),
    updated_at = NOW()
WHERE path LIKE '%trading-data/docs/07_layer_06_position_projection.md%';

UPDATE trading_registry
SET path = REPLACE(path, 'trading-data/docs/08_layer_07_underlying_action.md', 'trading-data/docs/07_layer_06_underlying_action.md'),
    updated_at = NOW()
WHERE path LIKE '%trading-data/docs/08_layer_07_underlying_action.md%';

UPDATE trading_registry
SET path = REPLACE(path, 'trading-data/docs/09_layer_08_option_expression.md', 'trading-data/docs/08_layer_07_trading_guidance.md'),
    updated_at = NOW()
WHERE path LIKE '%trading-data/docs/09_layer_08_option_expression.md%';
