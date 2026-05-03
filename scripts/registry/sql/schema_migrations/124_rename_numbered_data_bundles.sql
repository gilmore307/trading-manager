-- Numbered trading-data packages are data acquisition/preparation bundles for
-- model layers, not complete model-input universes. Rename registry payloads
-- and paths away from *_model_inputs to the bundle_XX_<layer> package names.

UPDATE trading_registry
SET key = 'BUNDLE_01_MARKET_REGIME',
    payload = 'bundle_01_market_regime',
    path = 'trading-data/src/trading_data/data_bundles/bundle_01_market_regime',
    note = '01 manager-facing MarketRegimeModel data bundle; fetches ETF bars required from data sources and writes model_inputs.market_regime_etf_bar'
WHERE key = '01_MARKET_REGIME_MODEL_INPUTS';

UPDATE trading_registry
SET key = 'BUNDLE_02_SECURITY_SELECTION',
    payload = 'bundle_02_security_selection',
    path = 'trading-data/src/trading_data/data_bundles/bundle_02_security_selection',
    note = '02 manager-facing SecuritySelectionModel data bundle; fetches ETF holdings required from data sources and writes model_inputs.security_selection_us_equity_etf_holding'
WHERE key = '02_SECURITY_SELECTION_MODEL_INPUTS';

UPDATE trading_registry
SET key = 'BUNDLE_03_STRATEGY_SELECTION',
    payload = 'bundle_03_strategy_selection',
    path = 'trading-data/src/trading_data/data_bundles/bundle_03_strategy_selection',
    note = '03 manager-facing StrategySelectionModel data bundle; fetches bars and liquidity required from data sources and writes model_inputs.strategy_selection_symbol_bar_liquidity'
WHERE key = '03_STRATEGY_SELECTION_MODEL_INPUTS';

UPDATE trading_registry
SET key = 'BUNDLE_05_OPTION_EXPRESSION',
    payload = 'bundle_05_option_expression',
    path = 'trading-data/src/trading_data/data_bundles/bundle_05_option_expression',
    note = '05 manager-facing OptionExpressionModel data bundle; fetches option snapshots required from data sources and writes the option-expression SQL contract'
WHERE key = '05_OPTION_EXPRESSION_MODEL_INPUTS';

UPDATE trading_registry
SET key = 'BUNDLE_06_POSITION_EXECUTION',
    payload = 'bundle_06_position_execution',
    path = 'trading-data/src/trading_data/data_bundles/bundle_06_position_execution',
    note = '06 manager-facing PositionExecutionModel data bundle; fetches selected-contract option time series required from data sources and writes model_inputs.position_execution_option_contract_timeseries'
WHERE key = '06_POSITION_EXECUTION_MODEL_INPUTS';

UPDATE trading_registry
SET key = 'BUNDLE_07_EVENT_OVERLAY',
    payload = 'bundle_07_event_overlay',
    path = 'trading-data/src/trading_data/data_bundles/bundle_07_event_overlay',
    note = '07 manager-facing EventOverlayModel data bundle; prepares one SQL event overview row per required event with details behind references'
WHERE key = '07_EVENT_OVERLAY_MODEL_INPUTS';
