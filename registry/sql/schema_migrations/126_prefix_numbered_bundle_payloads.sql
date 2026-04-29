-- Keep the layer number first in numbered data-bundle package names so
-- filesystem order and semantic order match: NN_bundle_<layer>.

UPDATE trading_registry
SET key = '01_BUNDLE_MARKET_REGIME',
    payload = '01_bundle_market_regime',
    path = 'trading-data/src/trading_data/data_bundles/01_bundle_market_regime'
WHERE key = 'BUNDLE_01_MARKET_REGIME';

UPDATE trading_registry
SET key = '02_BUNDLE_SECURITY_SELECTION',
    payload = '02_bundle_security_selection',
    path = 'trading-data/src/trading_data/data_bundles/02_bundle_security_selection'
WHERE key = 'BUNDLE_02_SECURITY_SELECTION';

UPDATE trading_registry
SET key = '03_BUNDLE_STRATEGY_SELECTION',
    payload = '03_bundle_strategy_selection',
    path = 'trading-data/src/trading_data/data_bundles/03_bundle_strategy_selection'
WHERE key = 'BUNDLE_03_STRATEGY_SELECTION';

UPDATE trading_registry
SET key = '05_BUNDLE_OPTION_EXPRESSION',
    payload = '05_bundle_option_expression',
    path = 'trading-data/src/trading_data/data_bundles/05_bundle_option_expression'
WHERE key = 'BUNDLE_05_OPTION_EXPRESSION';

UPDATE trading_registry
SET key = '06_BUNDLE_POSITION_EXECUTION',
    payload = '06_bundle_position_execution',
    path = 'trading-data/src/trading_data/data_bundles/06_bundle_position_execution'
WHERE key = 'BUNDLE_06_POSITION_EXECUTION';

UPDATE trading_registry
SET key = '07_BUNDLE_EVENT_OVERLAY',
    payload = '07_bundle_event_overlay',
    path = 'trading-data/src/trading_data/data_bundles/07_bundle_event_overlay'
WHERE key = 'BUNDLE_07_EVENT_OVERLAY';
