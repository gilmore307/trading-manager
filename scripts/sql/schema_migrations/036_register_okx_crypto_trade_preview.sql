-- Register OKX crypto preview/template paths and quote-missing liquidity design.
-- Target engine: PostgreSQL.

UPDATE trading_registry
SET
  path = 'trading-data/templates/data_kinds/okx/crypto_trade.preview.csv',
  applies_to = 'okx_bars',
  note = 'OKX canonical crypto trade row normalized toward Alpaca-like trade features; template path points to preview CSV shape'
WHERE kind = 'data_kind'
  AND key = 'CRYPTO_TRADE';

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, note)
VALUES
  ('dki_OKXLIQBR', 'data_kind', 'CRYPTO_LIQUIDITY_BAR', 'text', 'crypto_liquidity_bar', 'trading-data/templates/data_kinds/okx/crypto_liquidity_bar.preview.csv', 'okx_bars', 'Candidate OKX crypto liquidity interval row normalized toward Alpaca-like liquidity features; quote-derived fields may be null/blank when no sampled order-book snapshots exist')
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
  path = NULL,
  applies_to = 'okx_bars',
  note = 'OKX ticker/top-of-book source category; not currently accepted as a standalone final saved data kind because quote-derived features may be absent or sampled separately'
WHERE kind = 'data_kind'
  AND key = 'CRYPTO_QUOTE';

UPDATE trading_registry
SET
  path = NULL,
  applies_to = 'okx_bars',
  note = 'OKX order-book source category; snapshots can form a time series only from collection start unless a historical order-book source is accepted'
WHERE kind = 'data_kind'
  AND key = 'CRYPTO_ORDER_BOOK';
