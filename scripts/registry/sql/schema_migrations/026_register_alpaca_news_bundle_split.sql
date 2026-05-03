-- Register Alpaca news as a separate data acquisition bundle from quote/trade market events.
-- Target engine: PostgreSQL.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, note)
VALUES
  ('trm_HSVF3M02', 'term', 'ALPACA_QUOTES_TRADES', 'text', 'Historical trading-data bundle for Alpaca stock and ETF quotes and trades, excluding news', 'https://docs.alpaca.markets/', 'trading-data', 'preferred bundle key is alpaca_quotes_trades; news is intentionally split into ALPACA_NEWS'),
  ('trm_FXFQVK64', 'term', 'ALPACA_NEWS', 'text', 'Historical trading-data bundle for Alpaca stock and ETF news data as a standalone source workflow', 'https://docs.alpaca.markets/', 'trading-data', 'preferred bundle key is alpaca_news; task/run IDs should use alpaca_news-specific prefixes')
ON CONFLICT (id) DO UPDATE
SET
  kind = EXCLUDED.kind,
  key = EXCLUDED.key,
  payload_format = EXCLUDED.payload_format,
  payload = EXCLUDED.payload,
  path = EXCLUDED.path,
  applies_to = EXCLUDED.applies_to,
  note = EXCLUDED.note;
