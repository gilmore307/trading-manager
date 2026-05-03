-- Use type-first names for manager-facing source and derived boundaries.
-- This aligns active registry payloads/paths/scopes with SQL-safe table names such
-- as source_01_market_regime and derived_01_market_regime.

UPDATE trading_registry
SET
    key = replace(replace(replace(replace(replace(replace(replace(replace(
        key,
        'DERIVED_01_MARKET_REGIME', 'DERIVED_01_MARKET_REGIME'),
        'SOURCE_01_MARKET_REGIME', 'SOURCE_01_MARKET_REGIME'),
        'SOURCE_02_SECURITY_SELECTION', 'SOURCE_02_SECURITY_SELECTION'),
        'SOURCE_03_STRATEGY_SELECTION', 'SOURCE_03_STRATEGY_SELECTION'),
        'SOURCE_05_OPTION_EXPRESSION', 'SOURCE_05_OPTION_EXPRESSION'),
        'SOURCE_06_POSITION_EXECUTION', 'SOURCE_06_POSITION_EXECUTION'),
        'SOURCE_07_EVENT_OVERLAY', 'SOURCE_07_EVENT_OVERLAY'),
        'DERIVED_01_MARKET_REGIME', 'DERIVED_01_MARKET_REGIME'),
    payload = replace(replace(replace(replace(replace(replace(replace(
        payload,
        'derived_01_market_regime', 'derived_01_market_regime'),
        'source_01_market_regime', 'source_01_market_regime'),
        'source_02_security_selection', 'source_02_security_selection'),
        'source_03_strategy_selection', 'source_03_strategy_selection'),
        'source_05_option_expression', 'source_05_option_expression'),
        'source_06_position_execution', 'source_06_position_execution'),
        'source_07_event_overlay', 'source_07_event_overlay'),
    path = replace(replace(replace(replace(replace(replace(replace(
        path,
        'derived_01_market_regime', 'derived_01_market_regime'),
        'source_01_market_regime', 'source_01_market_regime'),
        'source_02_security_selection', 'source_02_security_selection'),
        'source_03_strategy_selection', 'source_03_strategy_selection'),
        'source_05_option_expression', 'source_05_option_expression'),
        'source_06_position_execution', 'source_06_position_execution'),
        'source_07_event_overlay', 'source_07_event_overlay'),
    applies_to = replace(replace(replace(replace(replace(replace(replace(
        applies_to,
        'derived_01_market_regime', 'derived_01_market_regime'),
        'source_01_market_regime', 'source_01_market_regime'),
        'source_02_security_selection', 'source_02_security_selection'),
        'source_03_strategy_selection', 'source_03_strategy_selection'),
        'source_05_option_expression', 'source_05_option_expression'),
        'source_06_position_execution', 'source_06_position_execution'),
        'source_07_event_overlay', 'source_07_event_overlay'),
    note = replace(replace(replace(replace(replace(replace(replace(
        note,
        'derived_01_market_regime', 'derived_01_market_regime'),
        'source_01_market_regime', 'source_01_market_regime'),
        'source_02_security_selection', 'source_02_security_selection'),
        'source_03_strategy_selection', 'source_03_strategy_selection'),
        'source_05_option_expression', 'source_05_option_expression'),
        'source_06_position_execution', 'source_06_position_execution'),
        'source_07_event_overlay', 'source_07_event_overlay'),
    updated_at = CURRENT_TIMESTAMP;
