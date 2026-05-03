-- Bundle SQL outputs are trading-data bundle products, not complete model inputs.
-- Keep bundle-derived table names, but move qualified contract notes from the
-- misleading model_inputs schema to the trading_data schema.

UPDATE trading_registry
SET note = replace(note, 'model_inputs.trading_data_01_bundle_market_regime', 'trading_data.trading_data_01_bundle_market_regime')
WHERE note LIKE '%model_inputs.trading_data_01_bundle_market_regime%';

UPDATE trading_registry
SET note = replace(note, 'model_inputs.trading_data_02_bundle_security_selection', 'trading_data.trading_data_02_bundle_security_selection')
WHERE note LIKE '%model_inputs.trading_data_02_bundle_security_selection%';

UPDATE trading_registry
SET note = replace(note, 'model_inputs.trading_data_03_bundle_strategy_selection', 'trading_data.trading_data_03_bundle_strategy_selection')
WHERE note LIKE '%model_inputs.trading_data_03_bundle_strategy_selection%';

UPDATE trading_registry
SET note = replace(note, 'model_inputs.trading_data_05_bundle_option_expression', 'trading_data.trading_data_05_bundle_option_expression')
WHERE note LIKE '%model_inputs.trading_data_05_bundle_option_expression%';

UPDATE trading_registry
SET note = replace(note, 'model_inputs.trading_data_06_bundle_position_execution', 'trading_data.trading_data_06_bundle_position_execution')
WHERE note LIKE '%model_inputs.trading_data_06_bundle_position_execution%';

UPDATE trading_registry
SET note = replace(note, 'model_inputs.trading_data_07_bundle_event_overlay', 'trading_data.trading_data_07_bundle_event_overlay')
WHERE note LIKE '%model_inputs.trading_data_07_bundle_event_overlay%';
