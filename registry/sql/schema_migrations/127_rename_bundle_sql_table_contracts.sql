-- Bundle SQL tables should be named after the trading-data bundle that writes
-- them, not as if they were the complete model-input/training-data universe.

UPDATE trading_registry
SET applies_to = replace(applies_to, 'market_regime_etf_bar', 'trading_data_01_bundle_market_regime'),
    note = replace(note, 'market_regime_etf_bar', 'trading_data_01_bundle_market_regime')
WHERE applies_to LIKE '%market_regime_etf_bar%'
   OR note LIKE '%market_regime_etf_bar%';

UPDATE trading_registry
SET applies_to = replace(applies_to, 'security_selection_us_equity_etf_holding', 'trading_data_02_bundle_security_selection'),
    note = replace(note, 'security_selection_us_equity_etf_holding', 'trading_data_02_bundle_security_selection')
WHERE applies_to LIKE '%security_selection_us_equity_etf_holding%'
   OR note LIKE '%security_selection_us_equity_etf_holding%';

UPDATE trading_registry
SET applies_to = replace(applies_to, 'strategy_selection_symbol_bar_liquidity', 'trading_data_03_bundle_strategy_selection'),
    note = replace(note, 'strategy_selection_symbol_bar_liquidity', 'trading_data_03_bundle_strategy_selection')
WHERE applies_to LIKE '%strategy_selection_symbol_bar_liquidity%'
   OR note LIKE '%strategy_selection_symbol_bar_liquidity%';

UPDATE trading_registry
SET applies_to = replace(applies_to, 'option_expression_option_chain_snapshot', 'trading_data_05_bundle_option_expression'),
    note = replace(note, 'option_expression_option_chain_snapshot', 'trading_data_05_bundle_option_expression')
WHERE applies_to LIKE '%option_expression_option_chain_snapshot%'
   OR note LIKE '%option_expression_option_chain_snapshot%';

UPDATE trading_registry
SET applies_to = replace(applies_to, 'option_expression_contract_snapshot', 'trading_data_05_bundle_option_expression'),
    note = replace(note, 'option_expression_contract_snapshot', 'trading_data_05_bundle_option_expression')
WHERE applies_to LIKE '%option_expression_contract_snapshot%'
   OR note LIKE '%option_expression_contract_snapshot%';

UPDATE trading_registry
SET applies_to = replace(applies_to, 'position_execution_option_contract_timeseries', 'trading_data_06_bundle_position_execution'),
    note = replace(note, 'position_execution_option_contract_timeseries', 'trading_data_06_bundle_position_execution')
WHERE applies_to LIKE '%position_execution_option_contract_timeseries%'
   OR note LIKE '%position_execution_option_contract_timeseries%';

UPDATE trading_registry
SET applies_to = replace(applies_to, 'event_overlay_event', 'trading_data_07_bundle_event_overlay'),
    note = replace(note, 'event_overlay_event', 'trading_data_07_bundle_event_overlay')
WHERE applies_to LIKE '%event_overlay_event%'
   OR note LIKE '%event_overlay_event%';

UPDATE trading_registry
SET note = replace(note, 'model_inputs.market_regime_etf_bar', 'model_inputs.trading_data_01_bundle_market_regime');
UPDATE trading_registry
SET note = replace(note, 'model_inputs.security_selection_us_equity_etf_holding', 'model_inputs.trading_data_02_bundle_security_selection');
UPDATE trading_registry
SET note = replace(note, 'model_inputs.strategy_selection_symbol_bar_liquidity', 'model_inputs.trading_data_03_bundle_strategy_selection');
UPDATE trading_registry
SET note = replace(note, 'model_inputs.option_expression_option_chain_snapshot', 'model_inputs.trading_data_05_bundle_option_expression');
UPDATE trading_registry
SET note = replace(note, 'model_inputs.position_execution_option_contract_timeseries', 'model_inputs.trading_data_06_bundle_position_execution');
UPDATE trading_registry
SET note = replace(note, 'model_inputs.event_overlay_event', 'model_inputs.trading_data_07_bundle_event_overlay');
