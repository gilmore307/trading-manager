-- Prune retired calendar_discovery route and obsolete macro provider reference
-- rows. Current macro/event inputs use accepted trading-data source interfaces
-- such as 07_source_trading_economics_calendar_web; old execution calendar
-- discovery and inactive official macro provider references should not remain
-- active registry vocabulary.

DELETE FROM trading_registry
WHERE key IN (
  'CALENDAR_DISCOVERY',
  'ECONOMIC_RELEASE_CALENDAR',
  'EQUITY_EARNINGS_CALENDAR',
  'FOMC_MEETING',
  'FOMC_MINUTES',
  'FOMC_SEP',
  'FOMC_STATEMENT',
  'MACRO_RELEASE_CALENDAR',
  'ECONOMIC_RELEASE_EVENT',
  'FOMC_CALENDAR',
  'NASDAQ_EARNINGS_CALENDAR',
  'BEA',
  'BLS',
  'CENSUS',
  'FRED',
  'US_TREASURY_FISCAL_DATA',
  'BEA_SECRET_ALIAS',
  'BLS_SECRET_ALIAS',
  'CENSUS_SECRET_ALIAS',
  'FRED_SECRET_ALIAS'
);

UPDATE trading_registry
SET applies_to = replace(replace(applies_to, ';calendar_discovery', ''), 'calendar_discovery;', '')
WHERE applies_to IS NOT NULL
  AND applies_to LIKE '%calendar_discovery%';

UPDATE trading_registry
SET applies_to = NULL
WHERE applies_to = 'calendar_discovery';
