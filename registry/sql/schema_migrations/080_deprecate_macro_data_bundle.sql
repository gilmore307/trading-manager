-- Deprecate the macro_data executable bundle while preserving official macro API secret aliases/config rows.
-- Target engine: PostgreSQL.

UPDATE trading_registry
SET path = NULL,
    applies_to = 'deprecated_macro_data;trading-data',
    artifact_sync_policy = 'registry_only',
    note = 'Deprecated/removed executable bundle. Macro model inputs now use trading_economics_calendar_web visible-page rows. Official macro API secret aliases may remain stored for optional future research but are not active manager task routes.'
WHERE id = 'dbu_0A8O6R01';

UPDATE trading_registry
SET applies_to = 'deprecated_macro_data_source_reference',
    artifact_sync_policy = 'registry_only',
    note = note || '; deprecated for active trading-data manager routing because Trading Economics visible-page rows now replace macro_data for macro model inputs'
WHERE key IN (
  'MACRO_BLS_CPI',
  'MACRO_BLS_PPI',
  'MACRO_BLS_IMPORT_EXPORT_PRICES',
  'MACRO_BLS_EMPLOYMENT_PAYROLLS',
  'MACRO_BLS_LABOR_FORCE',
  'MACRO_BLS_JOLTS',
  'MACRO_BLS_ECI',
  'MACRO_BLS_PRODUCTIVITY',
  'MACRO_CENSUS_RETAIL_SALES',
  'MACRO_CENSUS_WHOLESALE_TRADE',
  'MACRO_CENSUS_MANUFACTURING_ORDERS',
  'MACRO_CENSUS_DURABLE_GOODS',
  'MACRO_CENSUS_CONSTRUCTION_SPENDING',
  'MACRO_CENSUS_HOUSING_CONSTRUCTION',
  'MACRO_CENSUS_NEW_HOME_SALES',
  'MACRO_CENSUS_BUSINESS_FORMATION',
  'MACRO_CENSUS_INTERNATIONAL_TRADE',
  'MACRO_BEA_NIPA',
  'MACRO_BEA_PCE_INCOME_OUTLAYS',
  'MACRO_BEA_GDP_BY_INDUSTRY',
  'MACRO_BEA_REGIONAL',
  'MACRO_BEA_INTERNATIONAL_ACCOUNTS',
  'MACRO_BEA_FIXED_ASSETS',
  'MACRO_TREASURY_DEBT',
  'MACRO_TREASURY_DTS',
  'MACRO_TREASURY_MTS',
  'MACRO_TREASURY_INTEREST_RATES',
  'MACRO_TREASURY_INTEREST_EXPENSE',
  'MACRO_FRED_NATIVE',
  'MACRO_ALFRED_VINTAGE'
);

UPDATE trading_registry
SET applies_to = 'deprecated_macro_data_transient_evidence',
    artifact_sync_policy = 'registry_only',
    note = 'Deprecated transient evidence shape from removed macro_data bundle. Do not route manager tasks here; macro model inputs now use trading_economics_calendar_event rows.'
WHERE id = 'dki_MACREL01';

UPDATE trading_registry
SET applies_to = 'trading_economics_calendar_web;event_database',
    note = 'Deprecated as a macro_data output path; macro model inputs now use trading_economics_calendar_event visible-page rows. Keep only as historical event-template reference until broader event cleanup.'
WHERE id = 'dki_MACREVT1';
