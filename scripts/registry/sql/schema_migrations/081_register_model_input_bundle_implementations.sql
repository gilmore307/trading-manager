-- Register manager-facing implementations and bundle-local configs for all seven model input bundles.
-- Target engine: PostgreSQL.

UPDATE trading_registry
SET path = 'trading-data/src/trading_data/data_bundles/market_regime_model_inputs',
    note = 'Implemented manager-facing MarketRegimeModel input manifest bundle with bundle-local config and point-in-time saved CSV output'
WHERE id = 'dbu_MRGINPUT';

UPDATE trading_registry
SET path = 'trading-data/src/trading_data/data_bundles/security_selection_model_inputs',
    note = 'Implemented manager-facing SecuritySelectionModel input manifest bundle with bundle-local config and point-in-time saved CSV output'
WHERE id = 'dbu_SECINPUT';

UPDATE trading_registry
SET path = 'trading-data/src/trading_data/data_bundles/strategy_selection_model_inputs',
    note = 'Implemented manager-facing StrategySelectionModel input manifest bundle with bundle-local config and point-in-time saved CSV output'
WHERE id = 'dbu_STRINPUT';

UPDATE trading_registry
SET path = 'trading-data/src/trading_data/data_bundles/trade_quality_model_inputs',
    note = 'Implemented manager-facing TradeQualityModel input manifest bundle with bundle-local config and point-in-time saved CSV output'
WHERE id = 'dbu_TRQINPUT';

UPDATE trading_registry
SET path = 'trading-data/src/trading_data/data_bundles/option_expression_model_inputs',
    note = 'Implemented manager-facing OptionExpressionModel input manifest bundle with bundle-local config and point-in-time saved CSV output; V1 supports long call/long put research only'
WHERE id = 'dbu_OPTINPUT';

UPDATE trading_registry
SET path = 'trading-data/src/trading_data/data_bundles/event_overlay_model_inputs',
    note = 'Implemented manager-facing EventOverlayModel input manifest bundle with bundle-local config and point-in-time saved CSV output; Trading Economics is the accepted macro input surface'
WHERE id = 'dbu_EVTINPUT';

UPDATE trading_registry
SET path = 'trading-data/src/trading_data/data_bundles/portfolio_risk_model_inputs',
    note = 'Implemented manager-facing PortfolioRiskModel input manifest bundle with bundle-local config and point-in-time saved CSV output; account/portfolio state remains execution/account-owned input evidence'
WHERE id = 'dbu_PRKINPUT';

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  ('cfg_MRGINPUT', 'config', 'MARKET_REGIME_MODEL_INPUTS_BUNDLE_CONFIG', 'json', '{"config":"bundle-local"}', 'trading-data/src/trading_data/data_bundles/market_regime_model_inputs/config.json', 'trading-data;market_regime_model_inputs', 'sync_artifact', 'Bundle-local config for MarketRegimeModel input roles and required source artifact kinds'),
  ('cfg_SECINPUT', 'config', 'SECURITY_SELECTION_MODEL_INPUTS_BUNDLE_CONFIG', 'json', '{"config":"bundle-local"}', 'trading-data/src/trading_data/data_bundles/security_selection_model_inputs/config.json', 'trading-data;security_selection_model_inputs', 'sync_artifact', 'Bundle-local config for SecuritySelectionModel input roles and required source/derived artifact kinds'),
  ('cfg_STRINPUT', 'config', 'STRATEGY_SELECTION_MODEL_INPUTS_BUNDLE_CONFIG', 'json', '{"config":"bundle-local"}', 'trading-data/src/trading_data/data_bundles/strategy_selection_model_inputs/config.json', 'trading-data;strategy_selection_model_inputs', 'sync_artifact', 'Bundle-local config for StrategySelectionModel input roles and required source/derived artifact kinds'),
  ('cfg_TRQINPUT', 'config', 'TRADE_QUALITY_MODEL_INPUTS_BUNDLE_CONFIG', 'json', '{"config":"bundle-local"}', 'trading-data/src/trading_data/data_bundles/trade_quality_model_inputs/config.json', 'trading-data;trade_quality_model_inputs', 'sync_artifact', 'Bundle-local config for TradeQualityModel input roles and required source/derived artifact kinds'),
  ('cfg_OPTINPUT', 'config', 'OPTION_EXPRESSION_MODEL_INPUTS_BUNDLE_CONFIG', 'json', '{"config":"bundle-local"}', 'trading-data/src/trading_data/data_bundles/option_expression_model_inputs/config.json', 'trading-data;option_expression_model_inputs', 'sync_artifact', 'Bundle-local config for OptionExpressionModel input roles and required source/derived artifact kinds'),
  ('cfg_EVTINPUT', 'config', 'EVENT_OVERLAY_MODEL_INPUTS_BUNDLE_CONFIG', 'json', '{"config":"bundle-local"}', 'trading-data/src/trading_data/data_bundles/event_overlay_model_inputs/config.json', 'trading-data;event_overlay_model_inputs', 'sync_artifact', 'Bundle-local config for EventOverlayModel input roles and required source/derived artifact kinds'),
  ('cfg_PRKINPUT', 'config', 'PORTFOLIO_RISK_MODEL_INPUTS_BUNDLE_CONFIG', 'json', '{"config":"bundle-local"}', 'trading-data/src/trading_data/data_bundles/portfolio_risk_model_inputs/config.json', 'trading-data;portfolio_risk_model_inputs', 'sync_artifact', 'Bundle-local config for PortfolioRiskModel input roles and required source/derived artifact kinds')
ON CONFLICT (id) DO UPDATE
SET kind = EXCLUDED.kind,
    key = EXCLUDED.key,
    payload_format = EXCLUDED.payload_format,
    payload = EXCLUDED.payload,
    path = EXCLUDED.path,
    applies_to = EXCLUDED.applies_to,
    artifact_sync_policy = EXCLUDED.artifact_sync_policy,
    note = EXCLUDED.note;
