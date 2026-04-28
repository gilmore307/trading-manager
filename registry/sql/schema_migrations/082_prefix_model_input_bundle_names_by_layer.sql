-- Prefix model-input data bundle implementation names/paths by trading-model layer number.
-- Target engine: PostgreSQL.

UPDATE trading_registry
SET key = 'LAYER01_MARKET_REGIME_MODEL_INPUTS',
    payload = 'layer01_market_regime_model_inputs',
    path = 'trading-data/src/trading_data/data_bundles/layer01_market_regime_model_inputs',
    note = 'Layer 01 manager-facing MarketRegimeModel input manifest bundle with bundle-local config and point-in-time saved CSV output'
WHERE id = 'dbu_MRGINPUT';

UPDATE trading_registry
SET key = 'LAYER02_SECURITY_SELECTION_MODEL_INPUTS',
    payload = 'layer02_security_selection_model_inputs',
    path = 'trading-data/src/trading_data/data_bundles/layer02_security_selection_model_inputs',
    note = 'Layer 02 manager-facing SecuritySelectionModel input manifest bundle with bundle-local config and point-in-time saved CSV output'
WHERE id = 'dbu_SECINPUT';

UPDATE trading_registry
SET key = 'LAYER03_STRATEGY_SELECTION_MODEL_INPUTS',
    payload = 'layer03_strategy_selection_model_inputs',
    path = 'trading-data/src/trading_data/data_bundles/layer03_strategy_selection_model_inputs',
    note = 'Layer 03 manager-facing StrategySelectionModel input manifest bundle with bundle-local config and point-in-time saved CSV output'
WHERE id = 'dbu_STRINPUT';

UPDATE trading_registry
SET key = 'LAYER04_TRADE_QUALITY_MODEL_INPUTS',
    payload = 'layer04_trade_quality_model_inputs',
    path = 'trading-data/src/trading_data/data_bundles/layer04_trade_quality_model_inputs',
    note = 'Layer 04 manager-facing TradeQualityModel input manifest bundle with bundle-local config and point-in-time saved CSV output'
WHERE id = 'dbu_TRQINPUT';

UPDATE trading_registry
SET key = 'LAYER05_OPTION_EXPRESSION_MODEL_INPUTS',
    payload = 'layer05_option_expression_model_inputs',
    path = 'trading-data/src/trading_data/data_bundles/layer05_option_expression_model_inputs',
    note = 'Layer 05 manager-facing OptionExpressionModel input manifest bundle with bundle-local config and point-in-time saved CSV output; V1 supports long call/long put research only'
WHERE id = 'dbu_OPTINPUT';

UPDATE trading_registry
SET key = 'LAYER06_EVENT_OVERLAY_MODEL_INPUTS',
    payload = 'layer06_event_overlay_model_inputs',
    path = 'trading-data/src/trading_data/data_bundles/layer06_event_overlay_model_inputs',
    note = 'Layer 06 manager-facing EventOverlayModel input manifest bundle with bundle-local config and point-in-time saved CSV output; Trading Economics is the accepted macro input surface'
WHERE id = 'dbu_EVTINPUT';

UPDATE trading_registry
SET key = 'LAYER07_PORTFOLIO_RISK_MODEL_INPUTS',
    payload = 'layer07_portfolio_risk_model_inputs',
    path = 'trading-data/src/trading_data/data_bundles/layer07_portfolio_risk_model_inputs',
    note = 'Layer 07 manager-facing PortfolioRiskModel input manifest bundle with bundle-local config and point-in-time saved CSV output; account/portfolio state remains execution/account-owned input evidence'
WHERE id = 'dbu_PRKINPUT';

UPDATE trading_registry
SET key = 'LAYER01_MARKET_REGIME_MODEL_INPUTS_BUNDLE_CONFIG',
    path = 'trading-data/src/trading_data/data_bundles/layer01_market_regime_model_inputs/config.json',
    applies_to = 'trading-data;layer01_market_regime_model_inputs',
    note = 'Bundle-local config for Layer 01 MarketRegimeModel input roles and required source artifact kinds'
WHERE id = 'cfg_MRGINPUT';

UPDATE trading_registry
SET key = 'LAYER02_SECURITY_SELECTION_MODEL_INPUTS_BUNDLE_CONFIG',
    path = 'trading-data/src/trading_data/data_bundles/layer02_security_selection_model_inputs/config.json',
    applies_to = 'trading-data;layer02_security_selection_model_inputs',
    note = 'Bundle-local config for Layer 02 SecuritySelectionModel input roles and required source/derived artifact kinds'
WHERE id = 'cfg_SECINPUT';

UPDATE trading_registry
SET key = 'LAYER03_STRATEGY_SELECTION_MODEL_INPUTS_BUNDLE_CONFIG',
    path = 'trading-data/src/trading_data/data_bundles/layer03_strategy_selection_model_inputs/config.json',
    applies_to = 'trading-data;layer03_strategy_selection_model_inputs',
    note = 'Bundle-local config for Layer 03 StrategySelectionModel input roles and required source/derived artifact kinds'
WHERE id = 'cfg_STRINPUT';

UPDATE trading_registry
SET key = 'LAYER04_TRADE_QUALITY_MODEL_INPUTS_BUNDLE_CONFIG',
    path = 'trading-data/src/trading_data/data_bundles/layer04_trade_quality_model_inputs/config.json',
    applies_to = 'trading-data;layer04_trade_quality_model_inputs',
    note = 'Bundle-local config for Layer 04 TradeQualityModel input roles and required source/derived artifact kinds'
WHERE id = 'cfg_TRQINPUT';

UPDATE trading_registry
SET key = 'LAYER05_OPTION_EXPRESSION_MODEL_INPUTS_BUNDLE_CONFIG',
    path = 'trading-data/src/trading_data/data_bundles/layer05_option_expression_model_inputs/config.json',
    applies_to = 'trading-data;layer05_option_expression_model_inputs',
    note = 'Bundle-local config for Layer 05 OptionExpressionModel input roles and required source/derived artifact kinds'
WHERE id = 'cfg_OPTINPUT';

UPDATE trading_registry
SET key = 'LAYER06_EVENT_OVERLAY_MODEL_INPUTS_BUNDLE_CONFIG',
    path = 'trading-data/src/trading_data/data_bundles/layer06_event_overlay_model_inputs/config.json',
    applies_to = 'trading-data;layer06_event_overlay_model_inputs',
    note = 'Bundle-local config for Layer 06 EventOverlayModel input roles and required source/derived artifact kinds'
WHERE id = 'cfg_EVTINPUT';

UPDATE trading_registry
SET key = 'LAYER07_PORTFOLIO_RISK_MODEL_INPUTS_BUNDLE_CONFIG',
    path = 'trading-data/src/trading_data/data_bundles/layer07_portfolio_risk_model_inputs/config.json',
    applies_to = 'trading-data;layer07_portfolio_risk_model_inputs',
    note = 'Bundle-local config for Layer 07 PortfolioRiskModel input roles and required source/derived artifact kinds'
WHERE id = 'cfg_PRKINPUT';
