-- Reclassify template/source rows and restrict data_kind to active final saved shapes.

ALTER TABLE trading_registry
DROP CONSTRAINT IF EXISTS trading_registry_kind_check;

UPDATE trading_registry
SET
  kind = 'template',
  artifact_sync_policy = 'sync_artifact',
  note = note || ' Registry cleanup 2026-04-28: reclassified from output to template because the row identifies a checked-in template artifact.'
WHERE kind = 'output'
  AND key IN (
    'DATA_SOURCE_BUNDLE_README_TEMPLATE',
    'DATA_SOURCE_CLEAN_SPEC_TEMPLATE',
    'DATA_SOURCE_FETCH_SPEC_TEMPLATE',
    'DATA_SOURCE_FIXTURE_POLICY_TEMPLATE',
    'DATA_SOURCE_PIPELINE_TEMPLATE',
    'DATA_SOURCE_SAVE_SPEC_TEMPLATE',
    'DATA_TASK_COMPLETION_RECEIPT_TEMPLATE',
    'DATA_TASK_KEY_TEMPLATE'
  );

UPDATE trading_registry
SET
  kind = 'script',
  payload = 'trading_web_search.brave.BraveSearchClient.search',
  applies_to = 'trading-main;web_search_helper',
  artifact_sync_policy = 'sync_artifact',
  note = 'shared Python helper for code-level Brave Search API calls using BRAVE_SEARCH_SECRET_ALIAS via trading registry secret resolver'
WHERE kind = 'output'
  AND key = 'BRAVE_SEARCH_HELPER';

UPDATE trading_registry
SET
  kind = 'shared_artifact',
  artifact_sync_policy = 'sync_artifact',
  note = note || ' Registry cleanup 2026-04-28: reclassified from output to shared_artifact because this is a live shared CSV, not a template.'
WHERE kind = 'output'
  AND key = 'MARKET_ETF_UNIVERSE_SHARED_CSV';

UPDATE trading_registry
SET
  kind = 'data_source',
  artifact_sync_policy = 'sync_artifact',
  note = note || ' Registry cleanup 2026-04-28: reclassified from data_bundle to data_source because this row identifies a source adapter/interface rather than a manager-facing bundle.'
WHERE kind = 'data_bundle'
  AND key IN (
    'ALPACA_BARS',
    'ALPACA_LIQUIDITY',
    'ALPACA_NEWS',
    'CALENDAR_DISCOVERY',
    'ETF_HOLDINGS',
    'GDELT_NEWS',
    'OKX_CRYPTO_MARKET_DATA',
    'SEC_COMPANY_FINANCIALS',
    'THETADATA_OPTION_EVENT_TIMELINE',
    'THETADATA_OPTION_PRIMARY_TRACKING',
    'THETADATA_OPTION_SELECTION_SNAPSHOT',
    'TRADING_ECONOMICS_CALENDAR_WEB'
  );

DELETE FROM trading_registry
WHERE kind = 'data_bundle'
  AND key IN (
    'MACRO_DATA',
    'STOCK_ETF_EXPOSURE_BUNDLE_DEPRECATED'
  );

DELETE FROM trading_registry
WHERE kind = 'data_kind'
  AND (path IS NULL OR BTRIM(path) = '');

ALTER TABLE trading_registry
ADD CONSTRAINT trading_registry_kind_check
CHECK (kind IN (
  'field',
  'repo',
  'config',
  'term',
  'data_bundle',
  'data_source',
  'data_kind',
  'template',
  'shared_artifact',
  'script',
  'payload_format',
  'artifact_sync_policy',
  'artifact_type',
  'manifest_type',
  'ready_signal_type',
  'request_type',
  'task_lifecycle_state',
  'review_readiness',
  'acceptance_outcome',
  'test_status',
  'maintenance_status',
  'docs_status'
));
