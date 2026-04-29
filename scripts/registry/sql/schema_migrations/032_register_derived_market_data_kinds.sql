-- Register derived bar-aligned market data kinds.
-- Target engine: PostgreSQL.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, note)
VALUES
  ('dki_QT22ZHLV', 'data_kind', 'EQUITY_TRADE_BAR_DERIVED', 'text', 'equity_trade_bar_derived', NULL, 'alpaca_quotes_trades;alpaca_bars', 'Derived stock/ETF bar-aligned trade features aggregated from raw trades; raw trades are transient inputs and are not persisted by default'),
  ('dki_SS9YYGK4', 'data_kind', 'EQUITY_QUOTE_BAR_DERIVED', 'text', 'equity_quote_bar_derived', NULL, 'alpaca_quotes_trades;alpaca_bars', 'Derived stock/ETF bar-aligned quote/spread/depth features aggregated from raw quotes; raw quotes are transient inputs and are not persisted by default'),
  ('dki_KPI0NZ49', 'data_kind', 'EQUITY_MICROSTRUCTURE_BAR_DERIVED', 'text', 'equity_microstructure_bar_derived', NULL, 'alpaca_quotes_trades;alpaca_bars', 'Derived stock/ETF bar-aligned microstructure features from trades joined to quotes; persisted only after aggregation to an accepted ET-aligned timeframe')
ON CONFLICT (id) DO UPDATE
SET
  kind = EXCLUDED.kind,
  key = EXCLUDED.key,
  payload_format = EXCLUDED.payload_format,
  payload = EXCLUDED.payload,
  path = EXCLUDED.path,
  applies_to = EXCLUDED.applies_to,
  note = EXCLUDED.note;
