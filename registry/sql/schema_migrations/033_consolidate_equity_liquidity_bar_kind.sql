-- Consolidate Alpaca trade/quote derived output kinds into one final liquidity bar data kind.
-- Target engine: PostgreSQL.

DELETE FROM trading_registry
WHERE kind = 'data_kind'
  AND key IN (
    'EQUITY_TRADE_BAR_DERIVED',
    'EQUITY_QUOTE_BAR_DERIVED',
    'EQUITY_MICROSTRUCTURE_BAR_DERIVED'
  );

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, note)
VALUES
  ('dki_64LQWJCW', 'data_kind', 'EQUITY_LIQUIDITY_BAR', 'text', 'equity_liquidity_bar', NULL, 'alpaca_quotes_trades;alpaca_bars', 'Final persisted stock/ETF liquidity bar aggregated from transient raw trades and quotes; replaces separate trade/quote/microstructure derived outputs')
ON CONFLICT (id) DO UPDATE
SET
  kind = EXCLUDED.kind,
  key = EXCLUDED.key,
  payload_format = EXCLUDED.payload_format,
  payload = EXCLUDED.payload,
  path = EXCLUDED.path,
  applies_to = EXCLUDED.applies_to,
  note = EXCLUDED.note;
