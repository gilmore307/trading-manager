-- Register shared model-facing fields used by Alpaca/OKX market data and news/event timelines.
-- Target engine: PostgreSQL.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, note)
VALUES
  ('fld_MKT001', 'field', 'MARKET_SYMBOL', 'field_name', 'symbol', 'trading-data/templates/data_kinds/README.md', 'market_data_template', 'model-facing instrument symbol field shared by Alpaca and OKX market outputs'),
  ('fld_MKT002', 'field', 'MARKET_INTERVAL_START_ET', 'field_name', 'interval_start_et', 'trading-data/templates/data_kinds/README.md', 'market_liquidity_template', 'interval start timestamp in America/New_York for market liquidity bars'),
  ('fld_MKT003', 'field', 'MARKET_TRADE_COUNT', 'field_name', 'trade_count', 'trading-data/templates/data_kinds/README.md', 'market_data_template', 'number of trades contributing to a bar or liquidity interval'),
  ('fld_MKT004', 'field', 'MARKET_QUOTE_COUNT', 'field_name', 'quote_count', 'trading-data/templates/data_kinds/README.md', 'market_liquidity_template', 'number of quotes contributing to a liquidity interval; may be blank when quote history is unavailable'),
  ('fld_MKT005', 'field', 'MARKET_TRADE_VOLUME', 'field_name', 'trade_volume', 'trading-data/templates/data_kinds/README.md', 'market_liquidity_template', 'trade volume contributing to a liquidity interval'),
  ('fld_MKT006', 'field', 'MARKET_TRADE_VWAP', 'field_name', 'trade_vwap', 'trading-data/templates/data_kinds/README.md', 'market_liquidity_template', 'trade volume-weighted average price in a liquidity interval'),
  ('fld_MKT007', 'field', 'MARKET_TRADE_OPEN', 'field_name', 'trade_open', 'trading-data/templates/data_kinds/README.md', 'market_liquidity_template', 'first trade price in a liquidity interval'),
  ('fld_MKT008', 'field', 'MARKET_TRADE_HIGH', 'field_name', 'trade_high', 'trading-data/templates/data_kinds/README.md', 'market_liquidity_template', 'highest trade price in a liquidity interval'),
  ('fld_MKT009', 'field', 'MARKET_TRADE_LOW', 'field_name', 'trade_low', 'trading-data/templates/data_kinds/README.md', 'market_liquidity_template', 'lowest trade price in a liquidity interval'),
  ('fld_MKT010', 'field', 'MARKET_TRADE_CLOSE', 'field_name', 'trade_close', 'trading-data/templates/data_kinds/README.md', 'market_liquidity_template', 'last trade price in a liquidity interval'),
  ('fld_MKT011', 'field', 'MARKET_AVG_BID', 'field_name', 'avg_bid', 'trading-data/templates/data_kinds/README.md', 'market_liquidity_template', 'average bid price in a liquidity interval'),
  ('fld_MKT012', 'field', 'MARKET_AVG_ASK', 'field_name', 'avg_ask', 'trading-data/templates/data_kinds/README.md', 'market_liquidity_template', 'average ask price in a liquidity interval'),
  ('fld_MKT013', 'field', 'MARKET_AVG_MID', 'field_name', 'avg_mid', 'trading-data/templates/data_kinds/README.md', 'market_liquidity_template', 'average midpoint price in a liquidity interval'),
  ('fld_MKT014', 'field', 'MARKET_AVG_SPREAD', 'field_name', 'avg_spread', 'trading-data/templates/data_kinds/README.md', 'market_liquidity_template', 'average bid-ask spread in a liquidity interval'),
  ('fld_MKT015', 'field', 'MARKET_LAST_BID', 'field_name', 'last_bid', 'trading-data/templates/data_kinds/README.md', 'market_liquidity_template', 'last bid price in a liquidity interval'),
  ('fld_MKT016', 'field', 'MARKET_LAST_ASK', 'field_name', 'last_ask', 'trading-data/templates/data_kinds/README.md', 'market_liquidity_template', 'last ask price in a liquidity interval'),
  ('fld_MKT017', 'field', 'MARKET_LAST_MID', 'field_name', 'last_mid', 'trading-data/templates/data_kinds/README.md', 'market_liquidity_template', 'last midpoint price in a liquidity interval'),
  ('fld_MKT018', 'field', 'MARKET_VWAP_MINUS_AVG_MID', 'field_name', 'vwap_minus_avg_mid', 'trading-data/templates/data_kinds/README.md', 'market_liquidity_template', 'trade VWAP minus average midpoint in a liquidity interval'),
  ('fld_EVT001', 'field', 'TIMELINE_HEADLINE', 'field_name', 'headline', 'trading-data/templates/data_kinds/README.md', 'event_timeline_template', 'human-readable headline shared by news and event timeline outputs'),
  ('fld_EVT002', 'field', 'TIMELINE_AUTHOR', 'field_name', 'author', 'trading-data/templates/data_kinds/README.md', 'event_timeline_template', 'author/source byline when available for news or event timeline outputs'),
  ('fld_EVT003', 'field', 'TIMELINE_CREATED_AT_ET', 'field_name', 'created_at_et', 'trading-data/templates/data_kinds/README.md', 'event_timeline_template', 'event/news creation timestamp in America/New_York'),
  ('fld_EVT004', 'field', 'TIMELINE_UPDATED_AT_ET', 'field_name', 'updated_at_et', 'trading-data/templates/data_kinds/README.md', 'event_timeline_template', 'event/news update timestamp in America/New_York'),
  ('fld_EVT005', 'field', 'TIMELINE_SYMBOLS', 'field_name', 'symbols', 'trading-data/templates/data_kinds/README.md', 'event_timeline_template', 'semicolon-separated symbols associated with a news/event timeline row'),
  ('fld_EVT006', 'field', 'TIMELINE_SUMMARY', 'field_name', 'summary', 'trading-data/templates/data_kinds/README.md', 'event_timeline_template', 'short human-readable event/news summary'),
  ('fld_EVT007', 'field', 'TIMELINE_URL', 'field_name', 'url', 'trading-data/templates/data_kinds/README.md', 'event_timeline_template', 'external URL when available for a news/event row'),
  ('fld_EVT008', 'field', 'TIMELINE_IMAGE_COUNT', 'field_name', 'image_count', 'trading-data/templates/data_kinds/README.md', 'event_timeline_template', 'count of referenced images/media when available')
ON CONFLICT (id) DO UPDATE
SET
  kind = EXCLUDED.kind,
  key = EXCLUDED.key,
  payload_format = EXCLUDED.payload_format,
  payload = EXCLUDED.payload,
  path = EXCLUDED.path,
  applies_to = EXCLUDED.applies_to,
  note = EXCLUDED.note;

UPDATE trading_registry
SET
  note = 'OKX crypto liquidity interval row uses the shared Alpaca-like market liquidity schema; raw trades are transient inputs and quote-derived fields may be blank when no sampled order-book snapshots exist'
WHERE kind = 'data_kind'
  AND key = 'CRYPTO_LIQUIDITY_BAR';
