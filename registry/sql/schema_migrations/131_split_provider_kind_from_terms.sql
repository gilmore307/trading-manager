-- Split provider/source-owner identities out of generic terms. Provider rows
-- name the external provider or authoritative source surface; source_capability
-- rows continue to name endpoint/record-family capabilities.

ALTER TABLE trading_registry DROP CONSTRAINT IF EXISTS trading_registry_kind_check;
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
  'data_bundle',
  'data_source',
  'source_capability',
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

UPDATE trading_registry
SET kind = 'provider',
    payload = 'alpaca',
    applies_to = 'trading-data;alpaca_bars;alpaca_liquidity;alpaca_news',
    note = 'provider/source-owner identity for Alpaca brokerage and market-data APIs; endpoint and record-family capabilities are registered separately as source_capability rows'
WHERE key = 'ALPACA';

UPDATE trading_registry
SET kind = 'provider',
    payload = 'fred',
    applies_to = 'trading-data;macro_research',
    note = 'provider/source-owner identity for FRED/St. Louis Fed/ALFRED-native data; use only for unique or explicitly approved FRED-native research series/groups and do not duplicate official-agency source routes'
WHERE key = 'FRED';

UPDATE trading_registry
SET kind = 'provider',
    payload = 'bea',
    applies_to = 'trading-data;macro_research',
    note = 'provider/source-owner identity for the US Bureau of Economic Analysis API; no active manager route unless explicitly revived'
WHERE key = 'BEA';

UPDATE trading_registry
SET kind = 'provider',
    payload = 'bls',
    applies_to = 'trading-data;macro_research',
    note = 'provider/source-owner identity for the US Bureau of Labor Statistics API; no active manager route unless explicitly revived'
WHERE key = 'BLS';

UPDATE trading_registry
SET kind = 'provider',
    payload = 'census',
    applies_to = 'trading-data;macro_research',
    note = 'provider/source-owner identity for the US Census API; no active manager route unless explicitly revived'
WHERE key = 'CENSUS';

UPDATE trading_registry
SET kind = 'provider',
    payload = 'gdelt',
    applies_to = 'trading-data;gdelt_news;event_database',
    note = 'provider/source-owner identity for The GDELT Project; GKG and other record-family capabilities belong in source_capability rows'
WHERE key = 'GDELT';

UPDATE trading_registry
SET kind = 'provider',
    payload = 'github',
    applies_to = 'git_operations',
    note = 'provider/source-owner identity for GitHub code hosting and git remote operations; credentials remain source-level secret aliases outside Git'
WHERE key = 'GITHUB';

UPDATE trading_registry
SET kind = 'provider',
    payload = 'okx',
    applies_to = 'trading-data;okx_crypto_market_data',
    note = 'provider/source-owner identity for OKX cryptocurrency exchange/API; market-data endpoint capabilities belong in source_capability rows'
WHERE key = 'OKX';

UPDATE trading_registry
SET kind = 'provider',
    payload = 'sec_edgar',
    applies_to = 'trading-data;sec_company_financials',
    note = 'authoritative provider/source surface for SEC EDGAR APIs and filings; companyfacts, submissions, XBRL frames, and filing document capabilities are source_capability rows'
WHERE key = 'SEC_EDGAR';

UPDATE trading_registry
SET kind = 'provider',
    payload = 'thetadata',
    applies_to = 'trading-data;thetadata_option_primary_tracking;thetadata_option_selection_snapshot;thetadata_option_event_timeline',
    note = 'provider/source-owner identity for ThetaData options market data; option endpoint and record-family capabilities are source_capability rows'
WHERE key = 'THETADATA';

UPDATE trading_registry
SET kind = 'provider',
    payload = 'trading_economics',
    applies_to = 'trading-data;trading_economics_calendar_web',
    note = 'provider/source-owner identity for Trading Economics; the visible calendar page capability is registered separately as source_capability'
WHERE key = 'TRADING_ECONOMICS';

UPDATE trading_registry
SET kind = 'provider',
    payload = 'us_treasury_fiscal_data',
    applies_to = 'trading-data;macro_research',
    note = 'provider/source-owner identity for U.S. Treasury Fiscal Data open API; no secret alias is registered because official docs describe the API as open/no-key'
WHERE key = 'US_TREASURY_FISCAL_DATA';
