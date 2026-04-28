-- Integrate stock_etf_exposure generation into the 02 SecuritySelectionModel inputs bundle.
-- Target engine: PostgreSQL.

UPDATE trading_registry
SET key = 'STOCK_ETF_EXPOSURE_BUNDLE_DEPRECATED',
    path = NULL,
    applies_to = 'trading-data;02_security_selection_model_inputs;stock_etf_exposure',
    artifact_sync_policy = 'registry_only',
    note = 'Deprecated standalone manager-facing stock_etf_exposure bundle. stock_etf_exposure is now generated inside 02_security_selection_model_inputs from saved ETF holdings snapshots when params.stock_etf_exposure is provided.'
WHERE id = 'dbu_STKETFEX';

UPDATE trading_registry
SET key = '02_SECURITY_SELECTION_STOCK_ETF_EXPOSURE_CONFIG',
    path = 'trading-data/src/trading_data/data_bundles/02_security_selection_model_inputs/config.json',
    applies_to = 'trading-data;02_security_selection_model_inputs;stock_etf_exposure',
    artifact_sync_policy = 'sync_artifact',
    note = 'stock_etf_exposure defaults now live inside 02_security_selection_model_inputs/config.json under the stock_etf_exposure section.'
WHERE id = 'cfg_STKETFEX';
