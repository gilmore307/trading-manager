-- The schema already names the trading_data ownership boundary. Drop the
-- redundant trading_data_ prefix from bundle table names while keeping SQL-safe
-- identifiers that start with bundle_ rather than a digit.

UPDATE trading_registry
SET applies_to = replace(applies_to, 'trading_data_01_bundle_market_regime', 'bundle_01_market_regime'),
    note = replace(replace(note, 'trading_data.trading_data_01_bundle_market_regime', 'trading_data.bundle_01_market_regime'), 'trading_data_01_bundle_market_regime', 'bundle_01_market_regime')
WHERE applies_to LIKE '%trading_data_01_bundle_market_regime%'
   OR note LIKE '%trading_data_01_bundle_market_regime%';

UPDATE trading_registry
SET applies_to = replace(applies_to, 'trading_data_02_bundle_security_selection', 'bundle_02_security_selection'),
    note = replace(replace(note, 'trading_data.trading_data_02_bundle_security_selection', 'trading_data.bundle_02_security_selection'), 'trading_data_02_bundle_security_selection', 'bundle_02_security_selection')
WHERE applies_to LIKE '%trading_data_02_bundle_security_selection%'
   OR note LIKE '%trading_data_02_bundle_security_selection%';

UPDATE trading_registry
SET applies_to = replace(applies_to, 'trading_data_03_bundle_strategy_selection', 'bundle_03_strategy_selection'),
    note = replace(replace(note, 'trading_data.trading_data_03_bundle_strategy_selection', 'trading_data.bundle_03_strategy_selection'), 'trading_data_03_bundle_strategy_selection', 'bundle_03_strategy_selection')
WHERE applies_to LIKE '%trading_data_03_bundle_strategy_selection%'
   OR note LIKE '%trading_data_03_bundle_strategy_selection%';

UPDATE trading_registry
SET applies_to = replace(applies_to, 'trading_data_05_bundle_option_expression', 'bundle_05_option_expression'),
    note = replace(replace(note, 'trading_data.trading_data_05_bundle_option_expression', 'trading_data.bundle_05_option_expression'), 'trading_data_05_bundle_option_expression', 'bundle_05_option_expression')
WHERE applies_to LIKE '%trading_data_05_bundle_option_expression%'
   OR note LIKE '%trading_data_05_bundle_option_expression%';

UPDATE trading_registry
SET applies_to = replace(applies_to, 'trading_data_06_bundle_position_execution', 'bundle_06_position_execution'),
    note = replace(replace(note, 'trading_data.trading_data_06_bundle_position_execution', 'trading_data.bundle_06_position_execution'), 'trading_data_06_bundle_position_execution', 'bundle_06_position_execution')
WHERE applies_to LIKE '%trading_data_06_bundle_position_execution%'
   OR note LIKE '%trading_data_06_bundle_position_execution%';

UPDATE trading_registry
SET applies_to = replace(applies_to, 'trading_data_07_bundle_event_overlay', 'bundle_07_event_overlay'),
    note = replace(replace(note, 'trading_data.trading_data_07_bundle_event_overlay', 'trading_data.bundle_07_event_overlay'), 'trading_data_07_bundle_event_overlay', 'bundle_07_event_overlay')
WHERE applies_to LIKE '%trading_data_07_bundle_event_overlay%'
   OR note LIKE '%trading_data_07_bundle_event_overlay%';
