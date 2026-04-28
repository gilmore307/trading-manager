-- Merge duplicate field rows that had identical payload field names but
-- scenario-specific registry rows. Consumers use stable registry ids, so
-- downstream code must be updated to the retained canonical ids in the same change.

UPDATE trading_registry
SET
  key = 'EVIDENCE_WINDOW',
  applies_to = 'equity_abnormal_activity_event_template;option_activity_event_detail_template',
  path = 'trading-data/storage/templates/data_kinds/events/README.md',
  note = 'canonical shared evidence-window field for abnormal-activity and option-event detail templates'
WHERE kind = 'field' AND key = 'ABNORMAL_ACTIVITY_EVIDENCE_WINDOW';

UPDATE trading_registry
SET
  key = 'SOURCE_REFS',
  applies_to = 'equity_abnormal_activity_event_template;option_activity_event_detail_template',
  path = 'trading-data/storage/templates/data_kinds/events/README.md',
  note = 'canonical compact source-reference field for event evidence templates'
WHERE kind = 'field' AND key = 'EQUITY_ABNORMAL_ACTIVITY_SOURCE_REFS';

UPDATE trading_registry
SET
  key = 'AS_OF_DATE',
  applies_to = 'etf_holding_snapshot_template;stock_etf_exposure_template',
  path = 'trading-data/storage/templates/data_kinds/README.md',
  note = 'canonical as-of date field for point-in-time data snapshots and derived exposures'
WHERE kind = 'field' AND key = 'ETF_HOLDINGS_AS_OF_DATE';

UPDATE trading_registry
SET
  key = 'SYMBOL',
  applies_to = 'market_data_template;market_etf_universe;trading_event_template;event_factor_template;event_analysis_report_template;stock_etf_exposure_template;trading_economics_calendar_event_template',
  path = 'trading-data/storage/templates/data_kinds/README.md',
  note = 'canonical symbol field for tradable instruments and symbol-bearing event/calendar rows'
WHERE kind = 'field' AND key = 'INSTRUMENT_SYMBOL';

UPDATE trading_registry
SET
  key = 'SOURCE_URL',
  applies_to = 'etf_holding_snapshot_template;trading_event_template;event_analysis_report_template;trading_economics_calendar_event_template',
  path = 'trading-data/storage/templates/data_kinds/README.md',
  note = 'canonical source URL field for evidence, source, and issuer-reference rows'
WHERE kind = 'field' AND key = 'EVENT_SOURCE_URL';

UPDATE trading_registry
SET
  key = 'TITLE',
  applies_to = 'trading_event_template;event_analysis_report_template;gdelt_article_template',
  path = 'trading-data/storage/templates/data_kinds/README.md',
  note = 'canonical short title/headline field for event and article-like rows'
WHERE kind = 'field' AND key = 'EVENT_TITLE';

UPDATE trading_registry
SET
  key = 'EVENT_TIME_ET',
  applies_to = 'trading_event_template;event_factor_template;trading_economics_calendar_event_template',
  path = 'trading-data/storage/templates/data_kinds/README.md',
  note = 'canonical source publication, detection, or calendar event timestamp normalized to America/New_York'
WHERE kind = 'field' AND key = 'EVENT_TIME_ET';

UPDATE trading_registry
SET
  key = 'SOURCE_TYPE',
  applies_to = 'trading_event_template;event_analysis_report_template;gdelt_article_template',
  path = 'trading-data/storage/templates/data_kinds/README.md',
  note = 'canonical source-family/type field for event and article evidence rows'
WHERE kind = 'field' AND key = 'EVENT_SOURCE_TYPE';

UPDATE trading_registry
SET
  key = 'SUMMARY',
  applies_to = 'trading_event_template;event_analysis_report_template;event_timeline_template',
  path = 'trading-data/storage/templates/data_kinds/README.md',
  note = 'canonical short summary field for event and timeline rows'
WHERE kind = 'field' AND key = 'EVENT_SUMMARY';

UPDATE trading_registry
SET
  key = 'URL',
  applies_to = 'event_timeline_template;gdelt_article_template',
  path = 'trading-data/storage/templates/data_kinds/README.md',
  note = 'canonical URL field for article, news, and event timeline rows'
WHERE kind = 'field' AND key = 'TIMELINE_URL';

UPDATE trading_registry
SET
  applies_to = 'trading_event_template;event_factor_template;event_analysis_report_template;option_activity_event_detail_template',
  path = 'trading-data/storage/templates/data_kinds/events/README.md',
  note = 'canonical stable event identifier shared across event rows, factors, analysis reports, and option event details'
WHERE kind = 'field' AND key = 'EVENT_ID';

DELETE FROM trading_registry
WHERE kind = 'field'
  AND key IN (
    'ETF_HOLDING_SOURCE_URL',
    'EVENT_SYMBOL',
    'GDELT_ARTICLE_TITLE',
    'GDELT_ARTICLE_URL',
    'GDELT_SOURCE_TYPE',
    'OPTION_EVENT_DETAIL_EVENT_ID',
    'OPTION_EVENT_DETAIL_EVIDENCE_WINDOW',
    'OPTION_EVENT_DETAIL_SOURCE_REFS',
    'STOCK_ETF_EXPOSURE_AS_OF_DATE',
    'STOCK_ETF_EXPOSURE_SYMBOL',
    'TIMELINE_SUMMARY',
    'TRADING_ECONOMICS_EVENT_TIME_ET',
    'TRADING_ECONOMICS_SOURCE_URL',
    'TRADING_ECONOMICS_SYMBOL'
  );
