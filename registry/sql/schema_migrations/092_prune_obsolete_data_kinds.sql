-- Prune obsolete data_kind rows and remove the leftover erroneous field row.
-- Rows removed here either had no active external consumer, represented deprecated
-- macro/source wishlist concepts, or were provider endpoint labels without a current
-- routeable contract or final saved template.

DELETE FROM trading_registry
WHERE kind = 'field'
  AND key = 'REGISTRY_ITEM_FIELD_CATEGORY';

DELETE FROM trading_registry
WHERE kind = 'data_kind'
  AND key IN (
    'ECONOMIC_RELEASE_EVENT',
    'EQUITY_EARNINGS_CALENDAR',
    'ETF_CONSTITUENT_WEIGHT',
    'ETF_FUND_METADATA',
    'FOMC_MINUTES',
    'FOMC_SEP',
    'FOMC_STATEMENT',
    'MACRO_BEA_FIXED_ASSETS',
    'MACRO_BEA_GDP_BY_INDUSTRY',
    'MACRO_BEA_INTERNATIONAL_ACCOUNTS',
    'MACRO_BEA_PCE_INCOME_OUTLAYS',
    'MACRO_BEA_REGIONAL',
    'MACRO_BLS_ECI',
    'MACRO_BLS_EMPLOYMENT_PAYROLLS',
    'MACRO_BLS_IMPORT_EXPORT_PRICES',
    'MACRO_BLS_JOLTS',
    'MACRO_BLS_LABOR_FORCE',
    'MACRO_BLS_PPI',
    'MACRO_BLS_PRODUCTIVITY',
    'MACRO_CENSUS_BUSINESS_FORMATION',
    'MACRO_CENSUS_CONSTRUCTION_SPENDING',
    'MACRO_CENSUS_DURABLE_GOODS',
    'MACRO_CENSUS_HOUSING_CONSTRUCTION',
    'MACRO_CENSUS_INTERNATIONAL_TRADE',
    'MACRO_CENSUS_MANUFACTURING_ORDERS',
    'MACRO_CENSUS_NEW_HOME_SALES',
    'MACRO_CENSUS_RETAIL_SALES',
    'MACRO_CENSUS_WHOLESALE_TRADE',
    'MACRO_TREASURY_DEBT',
    'MACRO_TREASURY_INTEREST_EXPENSE',
    'MACRO_TREASURY_INTEREST_RATES',
    'MACRO_TREASURY_MTS',
    'SEC_FILING_DOCUMENT'
  );

-- Provider documentation URLs do not belong in data_kind.path. Keep these as
-- source-interface data kinds only where a current source interface or pipeline
-- consumes the payload, and leave direct provider documentation on source/provider terms.
UPDATE trading_registry
SET
  path = NULL,
  applies_to = 'source_interfaces',
  note = note || ' Registry cleanup 2026-04-28: retained as a routeable source-interface/input contract, not a final saved template; provider documentation URL removed from data_kind.path.'
WHERE kind = 'data_kind'
  AND key IN (
    'FOMC_MEETING',
    'MACRO_RELEASE_CALENDAR',
    'OPTION_CONTRACT',
    'OPTION_EOD',
    'OPTION_GREEKS_FIRST_ORDER',
    'OPTION_GREEKS_SECOND_ORDER',
    'OPTION_GREEKS_THIRD_ORDER',
    'OPTION_IMPLIED_VOLATILITY',
    'OPTION_OHLC',
    'OPTION_OPEN_INTEREST',
    'OPTION_SNAPSHOT',
    'OPTION_TRADE_GREEKS',
    'SEC_COMPANY_CONCEPT',
    'SEC_COMPANY_FACT',
    'SEC_SUBMISSION',
    'SEC_XBRL_FRAME'
  );
