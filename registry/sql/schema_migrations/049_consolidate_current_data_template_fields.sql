-- Consolidate current final data-template field rows and remove stale renamed leaves.
-- Target engine: PostgreSQL.

-- Shared top-level final-output fields that were originally introduced as README template metadata.
UPDATE trading_registry
SET
  key = 'DATA_KIND',
  path = 'trading-data/templates/data_kinds/README.md',
  applies_to = 'data_kind_template;market_data_template;market_liquidity_template;event_timeline_template;option_bar_template;option_chain_snapshot_template;option_activity_event_detail_template',
  note = 'canonical data_kind field used in source README entries and final saved data outputs'
WHERE kind = 'field'
  AND key = 'DATA_KIND_TEMPLATE_DATA_KIND';

UPDATE trading_registry
SET
  key = 'SOURCE',
  path = 'trading-data/templates/data_kinds/README.md',
  applies_to = 'data_kind_template;market_data_template;market_liquidity_template;option_bar_template;option_chain_snapshot_template',
  note = 'provider/source field used in source README entries and final saved data outputs'
WHERE kind = 'field'
  AND key = 'DATA_KIND_TEMPLATE_SOURCE';

-- Shared bar/output fields across market and option bars.
UPDATE trading_registry
SET
  key = 'DATA_TIMEFRAME',
  path = 'trading-data/templates/data_kinds/README.md',
  applies_to = 'market_data_template;market_liquidity_template;option_bar_template;option_activity_event_detail_template;option_template',
  note = 'requested or output time grain such as 1Min, 30Min, or 1Day shared by market and option outputs'
WHERE kind = 'field'
  AND key = 'OPTION_TIMEFRAME';

UPDATE trading_registry
SET
  key = 'DATA_TIMESTAMP_ET',
  path = 'trading-data/templates/data_kinds/README.md',
  applies_to = 'market_data_template;option_bar_template;option_chain_snapshot_template',
  note = 'timestamp in America/New_York shared by final bar outputs and nested option snapshot contexts'
WHERE kind = 'field'
  AND key = 'OPTION_TIMESTAMP_ET';

UPDATE trading_registry
SET key = 'BAR_OPEN', path = 'trading-data/templates/data_kinds/README.md', applies_to = 'market_data_template;option_bar_template', note = 'bar open price shared by market and option bar outputs'
WHERE kind = 'field' AND key = 'OPTION_BAR_OPEN';
UPDATE trading_registry
SET key = 'BAR_HIGH', path = 'trading-data/templates/data_kinds/README.md', applies_to = 'market_data_template;option_bar_template', note = 'bar high price shared by market and option bar outputs'
WHERE kind = 'field' AND key = 'OPTION_BAR_HIGH';
UPDATE trading_registry
SET key = 'BAR_LOW', path = 'trading-data/templates/data_kinds/README.md', applies_to = 'market_data_template;option_bar_template', note = 'bar low price shared by market and option bar outputs'
WHERE kind = 'field' AND key = 'OPTION_BAR_LOW';
UPDATE trading_registry
SET key = 'BAR_CLOSE', path = 'trading-data/templates/data_kinds/README.md', applies_to = 'market_data_template;option_bar_template', note = 'bar close price shared by market and option bar outputs'
WHERE kind = 'field' AND key = 'OPTION_BAR_CLOSE';
UPDATE trading_registry
SET key = 'BAR_VOLUME', path = 'trading-data/templates/data_kinds/README.md', applies_to = 'market_data_template;option_bar_template', note = 'bar volume shared by market and option bar outputs'
WHERE kind = 'field' AND key = 'OPTION_BAR_VOLUME';
UPDATE trading_registry
SET key = 'BAR_VWAP', path = 'trading-data/templates/data_kinds/README.md', applies_to = 'market_data_template;option_bar_template', note = 'bar volume-weighted average price shared by market and option bar outputs'
WHERE kind = 'field' AND key = 'OPTION_BAR_VWAP';

-- Option fields whose earlier payloads collided with different nested meanings.
UPDATE trading_registry
SET
  path = 'trading-data/templates/data_kinds/thetadata/README.md',
  applies_to = 'option_template;option_bar_template;option_chain_snapshot_template;option_activity_event_detail_template',
  note = 'underlying equity symbol for ThetaData option outputs and option task parameters'
WHERE kind = 'field'
  AND key = 'OPTION_UNDERLYING';

UPDATE trading_registry
SET
  payload = 'underlying_context',
  note = 'nested underlying context object for one option contract in an option chain snapshot'
WHERE kind = 'field'
  AND key = 'OPTION_UNDERLYING_CONTEXT';

UPDATE trading_registry
SET
  path = 'trading-data/templates/data_kinds/thetadata/option_chain_snapshot.preview.json',
  applies_to = 'option_chain_snapshot_template',
  note = 'underlying price associated with an option contract in option chain snapshot context'
WHERE kind = 'field'
  AND key = 'OPTION_TEMPLATE_UNDERLYING_PRICE';

UPDATE trading_registry
SET
  path = 'trading-data/templates/data_kinds/thetadata/option_chain_snapshot.preview.json',
  applies_to = 'option_chain_snapshot_template',
  note = 'underlying price timestamp in America/New_York for option chain snapshot context'
WHERE kind = 'field'
  AND key = 'OPTION_UNDERLYING_TIMESTAMP_ET';

UPDATE trading_registry
SET
  payload = 'contract_symbol',
  note = 'human-readable option contract symbol for the emitted event detail artifact'
WHERE kind = 'field'
  AND key = 'OPTION_EVENT_DETAIL_CONTRACT_SYMBOL';

UPDATE trading_registry
SET
  key = 'OPTION_EVENT_DETAIL_TRADE_TIMESTAMP_ET',
  payload = 'trade_timestamp_et',
  note = 'triggering trade timestamp in America/New_York for the emitted option activity event detail'
WHERE kind = 'field'
  AND key = 'OPTION_EVENT_DETAIL_TIMESTAMP_ET';

UPDATE trading_registry
SET
  key = 'OPTION_EVENT_DETAIL_TRADE_SIZE',
  payload = 'trade_size',
  note = 'triggering trade size in the emitted option activity event detail'
WHERE kind = 'field'
  AND key = 'OPTION_EVENT_DETAIL_SIZE';

UPDATE trading_registry
SET
  applies_to = 'option_template;option_chain_snapshot_template;option_activity_event_detail_template',
  note = 'option implied volatility field used in option snapshots and event detail contexts'
WHERE kind = 'field'
  AND key = 'OPTION_TEMPLATE_IMPLIED_VOL';

DELETE FROM trading_registry
WHERE kind = 'field'
  AND key IN (
    'OPTION_EVENT_DETAIL_PRICE',
    'OPTION_EVENT_DETAIL_IMPLIED_VOL'
  );

-- Current final event/news and option snapshot fields that were missing from current registry coverage.
INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, note)
VALUES
  ('fld_EVT009', 'field', 'TIMELINE_ID', 'field_name', 'id', 'trading-data/templates/data_kinds/README.md', 'event_timeline_template', 'stable source/news/event id in shared event/news timeline rows'),
  ('fld_OPT060', 'field', 'OPTION_QUOTE_BID_EXCHANGE', 'field_name', 'bid_exchange', 'trading-data/templates/data_kinds/thetadata/option_chain_snapshot.preview.json', 'option_chain_snapshot_template', 'bid exchange code in nested option quote context'),
  ('fld_OPT061', 'field', 'OPTION_QUOTE_ASK_EXCHANGE', 'field_name', 'ask_exchange', 'trading-data/templates/data_kinds/thetadata/option_chain_snapshot.preview.json', 'option_chain_snapshot_template', 'ask exchange code in nested option quote context'),
  ('fld_OPT062', 'field', 'OPTION_QUOTE_BID_CONDITION', 'field_name', 'bid_condition', 'trading-data/templates/data_kinds/thetadata/option_chain_snapshot.preview.json', 'option_chain_snapshot_template', 'bid condition code in nested option quote context'),
  ('fld_OPT063', 'field', 'OPTION_QUOTE_ASK_CONDITION', 'field_name', 'ask_condition', 'trading-data/templates/data_kinds/thetadata/option_chain_snapshot.preview.json', 'option_chain_snapshot_template', 'ask condition code in nested option quote context'),
  ('fld_OPT064', 'field', 'OPTION_IV_ERROR', 'field_name', 'iv_error', 'trading-data/templates/data_kinds/thetadata/option_chain_snapshot.preview.json', 'option_chain_snapshot_template', 'ThetaData implied-volatility error/status value in nested option IV context'),
  ('fld_OPD055', 'field', 'OPTION_EVENT_DETAIL_QUOTE_TIMESTAMP_ET', 'field_name', 'quote_timestamp_et', 'trading-data/templates/data_kinds/thetadata/option_activity_event_detail.preview.json', 'option_activity_event_detail_template', 'quote timestamp in America/New_York for event-local quote context'),
  ('fld_OPD056', 'field', 'OPTION_EVENT_DETAIL_QUOTE_SPREAD', 'field_name', 'quote_spread', 'trading-data/templates/data_kinds/thetadata/option_activity_event_detail.preview.json', 'option_activity_event_detail_template', 'quote ask minus bid spread in event-local quote context')
ON CONFLICT (id) DO UPDATE
SET
  kind = EXCLUDED.kind,
  key = EXCLUDED.key,
  payload_format = EXCLUDED.payload_format,
  payload = EXCLUDED.payload,
  path = EXCLUDED.path,
  applies_to = EXCLUDED.applies_to,
  note = EXCLUDED.note;
