-- Correct migration 164 after active registry naming was intentionally changed
-- from number-first to type-first manager-facing source/derived names.

UPDATE trading_registry
SET
    key = replace(replace(replace(replace(replace(replace(replace(
        key,
        '01_DERIVED_MARKET_REGIME', 'DERIVED_01_MARKET_REGIME'),
        '01_SOURCE_MARKET_REGIME', 'SOURCE_01_MARKET_REGIME'),
        '02_SOURCE_SECURITY_SELECTION', 'SOURCE_02_SECURITY_SELECTION'),
        '03_SOURCE_STRATEGY_SELECTION', 'SOURCE_03_STRATEGY_SELECTION'),
        '05_SOURCE_OPTION_EXPRESSION', 'SOURCE_05_OPTION_EXPRESSION'),
        '06_SOURCE_POSITION_EXECUTION', 'SOURCE_06_POSITION_EXECUTION'),
        '07_SOURCE_EVENT_OVERLAY', 'SOURCE_07_EVENT_OVERLAY'),
    payload = replace(replace(replace(replace(replace(replace(replace(
        payload,
        '01_derived_market_regime', 'derived_01_market_regime'),
        '01_source_market_regime', 'source_01_market_regime'),
        '02_source_security_selection', 'source_02_security_selection'),
        '03_source_strategy_selection', 'source_03_strategy_selection'),
        '05_source_option_expression', 'source_05_option_expression'),
        '06_source_position_execution', 'source_06_position_execution'),
        '07_source_event_overlay', 'source_07_event_overlay'),
    path = replace(replace(replace(replace(replace(replace(replace(
        path,
        '01_derived_market_regime', 'derived_01_market_regime'),
        '01_source_market_regime', 'source_01_market_regime'),
        '02_source_security_selection', 'source_02_security_selection'),
        '03_source_strategy_selection', 'source_03_strategy_selection'),
        '05_source_option_expression', 'source_05_option_expression'),
        '06_source_position_execution', 'source_06_position_execution'),
        '07_source_event_overlay', 'source_07_event_overlay'),
    applies_to = replace(replace(replace(replace(replace(replace(replace(
        applies_to,
        '01_derived_market_regime', 'derived_01_market_regime'),
        '01_source_market_regime', 'source_01_market_regime'),
        '02_source_security_selection', 'source_02_security_selection'),
        '03_source_strategy_selection', 'source_03_strategy_selection'),
        '05_source_option_expression', 'source_05_option_expression'),
        '06_source_position_execution', 'source_06_position_execution'),
        '07_source_event_overlay', 'source_07_event_overlay'),
    note = replace(replace(replace(replace(replace(replace(replace(
        note,
        '01_derived_market_regime', 'derived_01_market_regime'),
        '01_source_market_regime', 'source_01_market_regime'),
        '02_source_security_selection', 'source_02_security_selection'),
        '03_source_strategy_selection', 'source_03_strategy_selection'),
        '05_source_option_expression', 'source_05_option_expression'),
        '06_source_position_execution', 'source_06_position_execution'),
        '07_source_event_overlay', 'source_07_event_overlay'),
    updated_at = CURRENT_TIMESTAMP;
