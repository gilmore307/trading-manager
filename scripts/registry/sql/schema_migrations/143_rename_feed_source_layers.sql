-- Rename trading-source internal data boundaries: provider/source-interface
-- rows become feeds, while manager-facing former bundles become sources.
-- Historical migrations keep their old names; this migration updates active
-- registry rows and the active kind constraint only.

ALTER TABLE trading_registry DROP CONSTRAINT IF EXISTS trading_registry_kind_check;

UPDATE trading_registry
SET kind = 'data_feed'
WHERE kind = 'data_source';

UPDATE trading_registry
SET kind = 'data_source'
WHERE kind = 'data_bundle';

UPDATE trading_registry
SET kind = 'feed_capability'
WHERE kind = 'source_capability';

UPDATE trading_registry
SET
    key = replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(key, 'source_availability', 'feed_availability'), 'source_interfaces', 'feed_interfaces'), 'SOURCE_AVAILABILITY', 'FEED_AVAILABILITY'), 'SOURCE_INTERFACES', 'FEED_INTERFACES'), 'source_capability', 'feed_capability'), 'Source capability', 'Feed capability'), 'Source Capability', 'Feed Capability'), 'source capability', 'feed capability'), 'data_bundles', 'data_sources'), 'DATA_BUNDLE', 'DATA_SOURCE'), 'data_bundle', 'data_source'), '_BUNDLE_', '_SOURCE_'), 'trading-source-NN-bundle-', 'trading-source-NN-source-'), '01_source_alpaca_bars', '01_feed_alpaca_bars'), '02_source_alpaca_liquidity', '02_feed_alpaca_liquidity'), '03_source_alpaca_news', '03_feed_alpaca_news'), '04_source_okx_crypto_market_data', '04_feed_okx_crypto_market_data'), '05_source_gdelt_news', '05_feed_gdelt_news'), '06_source_etf_holdings', '06_feed_etf_holdings'), '07_source_trading_economics_calendar_web', '07_feed_trading_economics_calendar_web'), '08_source_sec_company_financials', '08_feed_sec_company_financials'), '09_source_thetadata_option_selection_snapshot', '09_feed_thetadata_option_selection_snapshot'), '10_source_thetadata_option_primary_tracking', '10_feed_thetadata_option_primary_tracking'), '11_source_thetadata_option_event_timeline', '11_feed_thetadata_option_event_timeline'), '01_bundle_market_regime', '01_source_market_regime'), '02_bundle_security_selection', '02_source_security_selection'), '03_bundle_strategy_selection', '03_source_strategy_selection'), '05_bundle_option_expression', '05_source_option_expression'), '06_bundle_position_execution', '06_source_position_execution'), '07_bundle_event_overlay', '07_source_event_overlay'), 'bundle_01_market_regime', 'source_01_market_regime'), 'bundle_02_security_selection', 'source_02_security_selection'), 'bundle_03_strategy_selection', 'source_03_strategy_selection'), 'bundle_05_option_expression', 'source_05_option_expression'), 'bundle_06_position_execution', 'source_06_position_execution'), 'bundle_07_event_overlay', 'source_07_event_overlay'),
    payload = replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(payload, 'source_availability', 'feed_availability'), 'source_interfaces', 'feed_interfaces'), 'SOURCE_AVAILABILITY', 'FEED_AVAILABILITY'), 'SOURCE_INTERFACES', 'FEED_INTERFACES'), 'source_capability', 'feed_capability'), 'Source capability', 'Feed capability'), 'Source Capability', 'Feed Capability'), 'source capability', 'feed capability'), 'data_bundles', 'data_sources'), 'DATA_BUNDLE', 'DATA_SOURCE'), 'data_bundle', 'data_source'), '_BUNDLE_', '_SOURCE_'), 'trading-source-NN-bundle-', 'trading-source-NN-source-'), '01_source_alpaca_bars', '01_feed_alpaca_bars'), '02_source_alpaca_liquidity', '02_feed_alpaca_liquidity'), '03_source_alpaca_news', '03_feed_alpaca_news'), '04_source_okx_crypto_market_data', '04_feed_okx_crypto_market_data'), '05_source_gdelt_news', '05_feed_gdelt_news'), '06_source_etf_holdings', '06_feed_etf_holdings'), '07_source_trading_economics_calendar_web', '07_feed_trading_economics_calendar_web'), '08_source_sec_company_financials', '08_feed_sec_company_financials'), '09_source_thetadata_option_selection_snapshot', '09_feed_thetadata_option_selection_snapshot'), '10_source_thetadata_option_primary_tracking', '10_feed_thetadata_option_primary_tracking'), '11_source_thetadata_option_event_timeline', '11_feed_thetadata_option_event_timeline'), '01_bundle_market_regime', '01_source_market_regime'), '02_bundle_security_selection', '02_source_security_selection'), '03_bundle_strategy_selection', '03_source_strategy_selection'), '05_bundle_option_expression', '05_source_option_expression'), '06_bundle_position_execution', '06_source_position_execution'), '07_bundle_event_overlay', '07_source_event_overlay'), 'bundle_01_market_regime', 'source_01_market_regime'), 'bundle_02_security_selection', 'source_02_security_selection'), 'bundle_03_strategy_selection', 'source_03_strategy_selection'), 'bundle_05_option_expression', 'source_05_option_expression'), 'bundle_06_position_execution', 'source_06_position_execution'), 'bundle_07_event_overlay', 'source_07_event_overlay'),
    path = replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(path, 'source_availability', 'feed_availability'), 'source_interfaces', 'feed_interfaces'), 'SOURCE_AVAILABILITY', 'FEED_AVAILABILITY'), 'SOURCE_INTERFACES', 'FEED_INTERFACES'), 'source_capability', 'feed_capability'), 'Source capability', 'Feed capability'), 'Source Capability', 'Feed Capability'), 'source capability', 'feed capability'), 'data_bundles', 'data_sources'), 'DATA_BUNDLE', 'DATA_SOURCE'), 'data_bundle', 'data_source'), '_BUNDLE_', '_SOURCE_'), 'trading-source-NN-bundle-', 'trading-source-NN-source-'), '01_source_alpaca_bars', '01_feed_alpaca_bars'), '02_source_alpaca_liquidity', '02_feed_alpaca_liquidity'), '03_source_alpaca_news', '03_feed_alpaca_news'), '04_source_okx_crypto_market_data', '04_feed_okx_crypto_market_data'), '05_source_gdelt_news', '05_feed_gdelt_news'), '06_source_etf_holdings', '06_feed_etf_holdings'), '07_source_trading_economics_calendar_web', '07_feed_trading_economics_calendar_web'), '08_source_sec_company_financials', '08_feed_sec_company_financials'), '09_source_thetadata_option_selection_snapshot', '09_feed_thetadata_option_selection_snapshot'), '10_source_thetadata_option_primary_tracking', '10_feed_thetadata_option_primary_tracking'), '11_source_thetadata_option_event_timeline', '11_feed_thetadata_option_event_timeline'), '01_bundle_market_regime', '01_source_market_regime'), '02_bundle_security_selection', '02_source_security_selection'), '03_bundle_strategy_selection', '03_source_strategy_selection'), '05_bundle_option_expression', '05_source_option_expression'), '06_bundle_position_execution', '06_source_position_execution'), '07_bundle_event_overlay', '07_source_event_overlay'), 'bundle_01_market_regime', 'source_01_market_regime'), 'bundle_02_security_selection', 'source_02_security_selection'), 'bundle_03_strategy_selection', 'source_03_strategy_selection'), 'bundle_05_option_expression', 'source_05_option_expression'), 'bundle_06_position_execution', 'source_06_position_execution'), 'bundle_07_event_overlay', 'source_07_event_overlay'),
    applies_to = replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(applies_to, 'source_availability', 'feed_availability'), 'source_interfaces', 'feed_interfaces'), 'SOURCE_AVAILABILITY', 'FEED_AVAILABILITY'), 'SOURCE_INTERFACES', 'FEED_INTERFACES'), 'source_capability', 'feed_capability'), 'Source capability', 'Feed capability'), 'Source Capability', 'Feed Capability'), 'source capability', 'feed capability'), 'data_bundles', 'data_sources'), 'DATA_BUNDLE', 'DATA_SOURCE'), 'data_bundle', 'data_source'), '_BUNDLE_', '_SOURCE_'), 'trading-source-NN-bundle-', 'trading-source-NN-source-'), '01_source_alpaca_bars', '01_feed_alpaca_bars'), '02_source_alpaca_liquidity', '02_feed_alpaca_liquidity'), '03_source_alpaca_news', '03_feed_alpaca_news'), '04_source_okx_crypto_market_data', '04_feed_okx_crypto_market_data'), '05_source_gdelt_news', '05_feed_gdelt_news'), '06_source_etf_holdings', '06_feed_etf_holdings'), '07_source_trading_economics_calendar_web', '07_feed_trading_economics_calendar_web'), '08_source_sec_company_financials', '08_feed_sec_company_financials'), '09_source_thetadata_option_selection_snapshot', '09_feed_thetadata_option_selection_snapshot'), '10_source_thetadata_option_primary_tracking', '10_feed_thetadata_option_primary_tracking'), '11_source_thetadata_option_event_timeline', '11_feed_thetadata_option_event_timeline'), '01_bundle_market_regime', '01_source_market_regime'), '02_bundle_security_selection', '02_source_security_selection'), '03_bundle_strategy_selection', '03_source_strategy_selection'), '05_bundle_option_expression', '05_source_option_expression'), '06_bundle_position_execution', '06_source_position_execution'), '07_bundle_event_overlay', '07_source_event_overlay'), 'bundle_01_market_regime', 'source_01_market_regime'), 'bundle_02_security_selection', 'source_02_security_selection'), 'bundle_03_strategy_selection', 'source_03_strategy_selection'), 'bundle_05_option_expression', 'source_05_option_expression'), 'bundle_06_position_execution', 'source_06_position_execution'), 'bundle_07_event_overlay', 'source_07_event_overlay'),
    note = replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(note, 'source_availability', 'feed_availability'), 'source_interfaces', 'feed_interfaces'), 'SOURCE_AVAILABILITY', 'FEED_AVAILABILITY'), 'SOURCE_INTERFACES', 'FEED_INTERFACES'), 'source_capability', 'feed_capability'), 'Source capability', 'Feed capability'), 'Source Capability', 'Feed Capability'), 'source capability', 'feed capability'), 'data_bundles', 'data_sources'), 'DATA_BUNDLE', 'DATA_SOURCE'), 'data_bundle', 'data_source'), '_BUNDLE_', '_SOURCE_'), 'trading-source-NN-bundle-', 'trading-source-NN-source-'), '01_source_alpaca_bars', '01_feed_alpaca_bars'), '02_source_alpaca_liquidity', '02_feed_alpaca_liquidity'), '03_source_alpaca_news', '03_feed_alpaca_news'), '04_source_okx_crypto_market_data', '04_feed_okx_crypto_market_data'), '05_source_gdelt_news', '05_feed_gdelt_news'), '06_source_etf_holdings', '06_feed_etf_holdings'), '07_source_trading_economics_calendar_web', '07_feed_trading_economics_calendar_web'), '08_source_sec_company_financials', '08_feed_sec_company_financials'), '09_source_thetadata_option_selection_snapshot', '09_feed_thetadata_option_selection_snapshot'), '10_source_thetadata_option_primary_tracking', '10_feed_thetadata_option_primary_tracking'), '11_source_thetadata_option_event_timeline', '11_feed_thetadata_option_event_timeline'), '01_bundle_market_regime', '01_source_market_regime'), '02_bundle_security_selection', '02_source_security_selection'), '03_bundle_strategy_selection', '03_source_strategy_selection'), '05_bundle_option_expression', '05_source_option_expression'), '06_bundle_position_execution', '06_source_position_execution'), '07_bundle_event_overlay', '07_source_event_overlay'), 'bundle_01_market_regime', 'source_01_market_regime'), 'bundle_02_security_selection', 'source_02_security_selection'), 'bundle_03_strategy_selection', 'source_03_strategy_selection'), 'bundle_05_option_expression', 'source_05_option_expression'), 'bundle_06_position_execution', 'source_06_position_execution'), 'bundle_07_event_overlay', 'source_07_event_overlay');

UPDATE trading_registry
SET note = replace(
             replace(
             replace(
             replace(
             replace(
             replace(
             replace(
             replace(
             replace(note,
               'source adapter/interface', 'feed connector/interface'),
               'source adapter', 'feed connector'),
               'Source interface', 'Feed interface'),
               'source interface', 'feed interface'),
               'data sources', 'data feeds'),
               'data source', 'data feed'),
               ' source evidence', ' feed evidence'),
               'source-evidence', 'feed-evidence'),
               ' bundle', ' feed')
WHERE kind = 'data_feed';

UPDATE trading_registry
SET note = replace(
             replace(note,
               'required from data sources', 'required from data feeds'),
               ' fetches bars and liquidity required from data sources', ' fetches bars and liquidity required from data feeds')
WHERE kind = 'data_source';

UPDATE trading_registry
SET note = replace(replace(note, 'Source', 'Feed'), 'source', 'feed')
WHERE kind = 'feed_capability';

UPDATE trading_registry
SET note = replace(
             replace(
             replace(note,
               'provider/source-owner', 'provider/feed-owner'),
               'source_capability', 'feed_capability'),
               'Source capability', 'Feed capability')
WHERE kind = 'provider';

ALTER TABLE trading_registry
ADD CONSTRAINT trading_registry_kind_check
CHECK (kind IN (
  'field',
  'identity_field',
  'path_field',
  'temporal_field',
  'classification_field',
  'text_field',
  'parameter_field',
  'repo',
  'config',
  'term',
  'provider',
  'data_feed',
  'data_source',
  'feed_capability',
  'data_kind',
  'template',
  'shared_artifact',
  'script',
  'payload_format',
  'status_value',
  'artifact_type',
  'manifest_type',
  'ready_signal_type',
  'request_type'
));
