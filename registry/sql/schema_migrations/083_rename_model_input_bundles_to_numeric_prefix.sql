-- Rename layer-prefixed model-input bundle registry rows to numeric folder prefixes.
-- Target engine: PostgreSQL.

UPDATE trading_registry
SET key = '01_MARKET_REGIME_MODEL_INPUTS',
    payload = '01_market_regime_model_inputs',
    path = 'trading-data/src/trading_data/data_bundles/01_market_regime_model_inputs',
    note = '01 manager-facing MarketRegimeModel input manifest bundle with bundle-local config and point-in-time saved CSV output'
WHERE id = 'dbu_MRGINPUT';

UPDATE trading_registry
SET key = '02_SECURITY_SELECTION_MODEL_INPUTS',
    payload = '02_security_selection_model_inputs',
    path = 'trading-data/src/trading_data/data_bundles/02_security_selection_model_inputs',
    note = '02 manager-facing SecuritySelectionModel input manifest bundle with bundle-local config and point-in-time saved CSV output'
WHERE id = 'dbu_SECINPUT';

UPDATE trading_registry
SET key = '03_STRATEGY_SELECTION_MODEL_INPUTS',
    payload = '03_strategy_selection_model_inputs',
    path = 'trading-data/src/trading_data/data_bundles/03_strategy_selection_model_inputs',
    note = '03 manager-facing StrategySelectionModel input manifest bundle with bundle-local config and point-in-time saved CSV output'
WHERE id = 'dbu_STRINPUT';

UPDATE trading_registry
SET key = '04_TRADE_QUALITY_MODEL_INPUTS',
    payload = '04_trade_quality_model_inputs',
    path = 'trading-data/src/trading_data/data_bundles/04_trade_quality_model_inputs',
    note = '04 manager-facing TradeQualityModel input manifest bundle with bundle-local config and point-in-time saved CSV output'
WHERE id = 'dbu_TRQINPUT';

UPDATE trading_registry
SET key = '05_OPTION_EXPRESSION_MODEL_INPUTS',
    payload = '05_option_expression_model_inputs',
    path = 'trading-data/src/trading_data/data_bundles/05_option_expression_model_inputs',
    note = '05 manager-facing OptionExpressionModel input manifest bundle with bundle-local config and point-in-time saved CSV output; V1 supports long call/long put research only'
WHERE id = 'dbu_OPTINPUT';

UPDATE trading_registry
SET key = '06_EVENT_OVERLAY_MODEL_INPUTS',
    payload = '06_event_overlay_model_inputs',
    path = 'trading-data/src/trading_data/data_bundles/06_event_overlay_model_inputs',
    note = '06 manager-facing EventOverlayModel input manifest bundle with bundle-local config and point-in-time saved CSV output; Trading Economics is the accepted macro input surface'
WHERE id = 'dbu_EVTINPUT';

UPDATE trading_registry
SET key = '07_PORTFOLIO_RISK_MODEL_INPUTS',
    payload = '07_portfolio_risk_model_inputs',
    path = 'trading-data/src/trading_data/data_bundles/07_portfolio_risk_model_inputs',
    note = '07 manager-facing PortfolioRiskModel input manifest bundle with bundle-local config and point-in-time saved CSV output; account/portfolio state remains execution/account-owned input evidence'
WHERE id = 'dbu_PRKINPUT';

UPDATE trading_registry
SET key = '01_MARKET_REGIME_MODEL_INPUTS_BUNDLE_CONFIG',
    path = 'trading-data/src/trading_data/data_bundles/01_market_regime_model_inputs/config.json',
    applies_to = 'trading-data;01_market_regime_model_inputs',
    note = 'Bundle-local config for 01 MarketRegimeModel input roles and required source artifact kinds'
WHERE id = 'cfg_MRGINPUT';

UPDATE trading_registry
SET key = '02_SECURITY_SELECTION_MODEL_INPUTS_BUNDLE_CONFIG',
    path = 'trading-data/src/trading_data/data_bundles/02_security_selection_model_inputs/config.json',
    applies_to = 'trading-data;02_security_selection_model_inputs',
    note = 'Bundle-local config for 02 SecuritySelectionModel input roles and required source/derived artifact kinds'
WHERE id = 'cfg_SECINPUT';

UPDATE trading_registry
SET key = '03_STRATEGY_SELECTION_MODEL_INPUTS_BUNDLE_CONFIG',
    path = 'trading-data/src/trading_data/data_bundles/03_strategy_selection_model_inputs/config.json',
    applies_to = 'trading-data;03_strategy_selection_model_inputs',
    note = 'Bundle-local config for 03 StrategySelectionModel input roles and required source/derived artifact kinds'
WHERE id = 'cfg_STRINPUT';

UPDATE trading_registry
SET key = '04_TRADE_QUALITY_MODEL_INPUTS_BUNDLE_CONFIG',
    path = 'trading-data/src/trading_data/data_bundles/04_trade_quality_model_inputs/config.json',
    applies_to = 'trading-data;04_trade_quality_model_inputs',
    note = 'Bundle-local config for 04 TradeQualityModel input roles and required source/derived artifact kinds'
WHERE id = 'cfg_TRQINPUT';

UPDATE trading_registry
SET key = '05_OPTION_EXPRESSION_MODEL_INPUTS_BUNDLE_CONFIG',
    path = 'trading-data/src/trading_data/data_bundles/05_option_expression_model_inputs/config.json',
    applies_to = 'trading-data;05_option_expression_model_inputs',
    note = 'Bundle-local config for 05 OptionExpressionModel input roles and required source/derived artifact kinds'
WHERE id = 'cfg_OPTINPUT';

UPDATE trading_registry
SET key = '06_EVENT_OVERLAY_MODEL_INPUTS_BUNDLE_CONFIG',
    path = 'trading-data/src/trading_data/data_bundles/06_event_overlay_model_inputs/config.json',
    applies_to = 'trading-data;06_event_overlay_model_inputs',
    note = 'Bundle-local config for 06 EventOverlayModel input roles and required source/derived artifact kinds'
WHERE id = 'cfg_EVTINPUT';

UPDATE trading_registry
SET key = '07_PORTFOLIO_RISK_MODEL_INPUTS_BUNDLE_CONFIG',
    path = 'trading-data/src/trading_data/data_bundles/07_portfolio_risk_model_inputs/config.json',
    applies_to = 'trading-data;07_portfolio_risk_model_inputs',
    note = 'Bundle-local config for 07 PortfolioRiskModel input roles and required source/derived artifact kinds'
WHERE id = 'cfg_PRKINPUT';
