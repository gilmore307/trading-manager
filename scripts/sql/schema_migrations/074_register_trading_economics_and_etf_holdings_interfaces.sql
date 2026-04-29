-- Register Trading Economics web-calendar interface and ETF holdings implementation scaffold.
-- Target engine: PostgreSQL.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  ('trm_TECALWEB', 'term', 'TRADING_ECONOMICS', 'text', 'Trading Economics visible macro calendar web page', 'https://tradingeconomics.com/united-states/calendar', 'trading_economics_calendar_web;macro_release_event', 'sync_artifact', 'Visible web-page macro calendar source for actual/previous/consensus/forecast fields; no API/download/export use under Basic-plan constraints'),
  ('dbu_TECALWEB', 'data_bundle', 'TRADING_ECONOMICS_CALENDAR_WEB', 'text', 'trading_economics_calendar_web', 'trading-data/src/trading_data/data_sources/trading_economics_calendar_web', 'trading-data', 'sync_artifact', 'Conservative Trading Economics visible-page interface/parser for U.S. high-impact macro calendar rows; no bulk backfill yet'),
  ('dki_TECALWEB', 'data_kind', 'TRADING_ECONOMICS_CALENDAR_EVENT', 'text', 'trading_economics_calendar_event', 'trading-data/storage/templates/data_kinds/trading_economics/trading_economics_calendar_event.preview.csv', 'trading_economics_calendar_web', 'sync_artifact', 'Visible Trading Economics calendar row used to enrich macro release events with actual/previous/consensus/forecast fields'),
  ('fld_TEC001', 'field', 'TRADING_ECONOMICS_EVENT_TIME_ET', 'field_name', 'event_time_et', 'trading-data/storage/templates/data_kinds/trading_economics/trading_economics_calendar_event.preview.csv', 'trading_economics_calendar_event_template', 'sync_artifact', 'Trading Economics visible event date/time interpreted in America/New_York when the page row is U.S. calendar data'),
  ('fld_TEC002', 'field', 'TRADING_ECONOMICS_COUNTRY', 'field_name', 'country', 'trading-data/storage/templates/data_kinds/trading_economics/trading_economics_calendar_event.preview.csv', 'trading_economics_calendar_event_template', 'sync_artifact', 'Trading Economics calendar country label'),
  ('fld_TEC003', 'field', 'TRADING_ECONOMICS_EVENT', 'field_name', 'event', 'trading-data/storage/templates/data_kinds/trading_economics/trading_economics_calendar_event.preview.csv', 'trading_economics_calendar_event_template', 'sync_artifact', 'Trading Economics calendar event name'),
  ('fld_TEC004', 'field', 'TRADING_ECONOMICS_CATEGORY', 'field_name', 'category', 'trading-data/storage/templates/data_kinds/trading_economics/trading_economics_calendar_event.preview.csv', 'trading_economics_calendar_event_template', 'sync_artifact', 'Trading Economics macro event category label'),
  ('fld_TEC005', 'field', 'TRADING_ECONOMICS_REFERENCE', 'field_name', 'reference', 'trading-data/storage/templates/data_kinds/trading_economics/trading_economics_calendar_event.preview.csv', 'trading_economics_calendar_event_template', 'sync_artifact', 'Trading Economics calendar reference period'),
  ('fld_TEC006', 'field', 'TRADING_ECONOMICS_ACTUAL', 'field_name', 'actual', 'trading-data/storage/templates/data_kinds/trading_economics/trading_economics_calendar_event.preview.csv', 'trading_economics_calendar_event_template', 'sync_artifact', 'Visible actual value from Trading Economics calendar row'),
  ('fld_TEC007', 'field', 'TRADING_ECONOMICS_PREVIOUS', 'field_name', 'previous', 'trading-data/storage/templates/data_kinds/trading_economics/trading_economics_calendar_event.preview.csv', 'trading_economics_calendar_event_template', 'sync_artifact', 'Visible previous value from Trading Economics calendar row'),
  ('fld_TEC008', 'field', 'TRADING_ECONOMICS_CONSENSUS', 'field_name', 'consensus', 'trading-data/storage/templates/data_kinds/trading_economics/trading_economics_calendar_event.preview.csv', 'trading_economics_calendar_event_template', 'sync_artifact', 'Visible consensus value from Trading Economics calendar row'),
  ('fld_TEC009', 'field', 'TRADING_ECONOMICS_FORECAST', 'field_name', 'te_forecast', 'trading-data/storage/templates/data_kinds/trading_economics/trading_economics_calendar_event.preview.csv', 'trading_economics_calendar_event_template', 'sync_artifact', 'Visible Trading Economics forecast value'),
  ('fld_TEC010', 'field', 'TRADING_ECONOMICS_REVISED', 'field_name', 'revised', 'trading-data/storage/templates/data_kinds/trading_economics/trading_economics_calendar_event.preview.csv', 'trading_economics_calendar_event_template', 'sync_artifact', 'Visible revised value from Trading Economics calendar row'),
  ('fld_TEC011', 'field', 'TRADING_ECONOMICS_IMPORTANCE', 'field_name', 'importance', 'trading-data/storage/templates/data_kinds/trading_economics/trading_economics_calendar_event.preview.csv', 'trading_economics_calendar_event_template', 'sync_artifact', 'Trading Economics calendar importance filter/value; first version uses 3 for high impact'),
  ('fld_TEC012', 'field', 'TRADING_ECONOMICS_SYMBOL', 'field_name', 'symbol', 'trading-data/storage/templates/data_kinds/trading_economics/trading_economics_calendar_event.preview.csv', 'trading_economics_calendar_event_template', 'sync_artifact', 'Trading Economics calendar symbol if visible on the row'),
  ('fld_TEC013', 'field', 'TRADING_ECONOMICS_SOURCE_URL', 'field_name', 'source_url', 'trading-data/storage/templates/data_kinds/trading_economics/trading_economics_calendar_event.preview.csv', 'trading_economics_calendar_event_template', 'sync_artifact', 'Trading Economics visible page URL used for the row'),
  ('fld_ETFH001', 'field', 'ETF_TICKER', 'field_name', 'etf_ticker', 'trading-data/storage/templates/data_kinds/etf/etf_holding_snapshot.preview.csv', 'etf_holding_snapshot_template', 'sync_artifact', 'ETF ticker whose issuer-published holdings are represented'),
  ('fld_ETFH002', 'field', 'ETF_ISSUER', 'field_name', 'issuer', 'trading-data/storage/templates/data_kinds/etf/etf_holding_snapshot.preview.csv', 'etf_holding_snapshot_template', 'sync_artifact', 'ETF issuer/source adapter key'),
  ('fld_ETFH003', 'field', 'ETF_HOLDINGS_AS_OF_DATE', 'field_name', 'as_of_date', 'trading-data/storage/templates/data_kinds/etf/etf_holding_snapshot.preview.csv', 'etf_holding_snapshot_template', 'sync_artifact', 'Issuer holdings as-of date'),
  ('fld_ETFH004', 'field', 'ETF_HOLDING_TICKER', 'field_name', 'holding_ticker', 'trading-data/storage/templates/data_kinds/etf/etf_holding_snapshot.preview.csv', 'etf_holding_snapshot_template', 'sync_artifact', 'Constituent ticker or issuer symbol'),
  ('fld_ETFH005', 'field', 'ETF_HOLDING_NAME', 'field_name', 'holding_name', 'trading-data/storage/templates/data_kinds/etf/etf_holding_snapshot.preview.csv', 'etf_holding_snapshot_template', 'sync_artifact', 'Constituent security name'),
  ('fld_ETFH006', 'field', 'ETF_HOLDING_WEIGHT', 'field_name', 'weight', 'trading-data/storage/templates/data_kinds/etf/etf_holding_snapshot.preview.csv', 'etf_holding_snapshot_template', 'sync_artifact', 'Constituent weight as a percentage of ETF net assets/fund value'),
  ('fld_ETFH007', 'field', 'ETF_HOLDING_SHARES', 'field_name', 'shares', 'trading-data/storage/templates/data_kinds/etf/etf_holding_snapshot.preview.csv', 'etf_holding_snapshot_template', 'sync_artifact', 'Issuer-published share count held by the ETF'),
  ('fld_ETFH008', 'field', 'ETF_HOLDING_MARKET_VALUE', 'field_name', 'market_value', 'trading-data/storage/templates/data_kinds/etf/etf_holding_snapshot.preview.csv', 'etf_holding_snapshot_template', 'sync_artifact', 'Issuer-published market value of the constituent holding'),
  ('fld_ETFH009', 'field', 'ETF_HOLDING_CUSIP', 'field_name', 'cusip', 'trading-data/storage/templates/data_kinds/etf/etf_holding_snapshot.preview.csv', 'etf_holding_snapshot_template', 'sync_artifact', 'Constituent CUSIP when issuer publishes it'),
  ('fld_ETFH010', 'field', 'ETF_HOLDING_SEDOL', 'field_name', 'sedol', 'trading-data/storage/templates/data_kinds/etf/etf_holding_snapshot.preview.csv', 'etf_holding_snapshot_template', 'sync_artifact', 'Constituent SEDOL when issuer publishes it'),
  ('fld_ETFH011', 'field', 'ETF_HOLDING_ASSET_CLASS', 'field_name', 'asset_class', 'trading-data/storage/templates/data_kinds/etf/etf_holding_snapshot.preview.csv', 'etf_holding_snapshot_template', 'sync_artifact', 'Issuer-published constituent asset class'),
  ('fld_ETFH012', 'field', 'ETF_HOLDING_SECTOR', 'field_name', 'sector', 'trading-data/storage/templates/data_kinds/etf/etf_holding_snapshot.preview.csv', 'etf_holding_snapshot_template', 'sync_artifact', 'Issuer-published constituent sector'),
  ('fld_ETFH013', 'field', 'ETF_HOLDING_SOURCE_URL', 'field_name', 'source_url', 'trading-data/storage/templates/data_kinds/etf/etf_holding_snapshot.preview.csv', 'etf_holding_snapshot_template', 'sync_artifact', 'Official issuer page/file URL used for the holdings row')
ON CONFLICT (id) DO UPDATE
SET kind = EXCLUDED.kind,
    key = EXCLUDED.key,
    payload_format = EXCLUDED.payload_format,
    payload = EXCLUDED.payload,
    path = EXCLUDED.path,
    applies_to = EXCLUDED.applies_to,
    artifact_sync_policy = EXCLUDED.artifact_sync_policy,
    note = EXCLUDED.note;

UPDATE trading_registry
SET path = 'trading-data/src/trading_data/data_sources/etf_holdings',
    artifact_sync_policy = 'sync_artifact',
    note = 'Issuer-site/source-file scaffold for ETF constituents and portfolio weights; user-owned ETF-to-issuer mapping will drive production routing'
WHERE kind = 'data_bundle' AND key = 'ETF_HOLDINGS';

UPDATE trading_registry
SET path = 'trading-data/storage/templates/data_kinds/etf/etf_holding_snapshot.preview.csv',
    artifact_sync_policy = 'sync_artifact',
    note = 'Final issuer-published ETF holdings snapshot row with normalized constituent ticker/name/weight/share/value fields'
WHERE kind = 'data_kind' AND key = 'ETF_HOLDINGS_SNAPSHOT';
