-- Rename the OKX bundle from bars-only to the accepted crypto market-data boundary.
-- Target engine: PostgreSQL.

UPDATE trading_registry
SET
  key = 'OKX_CRYPTO_MARKET_DATA',
  payload = 'okx_crypto_market_data',
  path = 'trading-data/src/trading_data/data_sources/okx_crypto_market_data',
  note = 'OKX canonical crypto market-data bundle for bars, normalized trades, and trade-derived liquidity bars; quote-derived liquidity fields may be null/blank when no sampled order-book snapshots exist'
WHERE id = 'dbu_W59XPQBY'
  AND kind = 'data_bundle';

UPDATE trading_registry
SET
  path = 'trading-data/templates/data_kinds/okx/crypto_bar.preview.csv',
  applies_to = 'okx_crypto_market_data',
  note = 'OKX canonical crypto OHLCV candle row; template path points to the accepted final CSV shape'
WHERE kind = 'data_kind'
  AND key = 'CRYPTO_BAR';

UPDATE trading_registry
SET applies_to = 'okx_crypto_market_data'
WHERE kind = 'data_kind'
  AND key IN ('CRYPTO_TRADE', 'CRYPTO_LIQUIDITY_BAR', 'CRYPTO_QUOTE', 'CRYPTO_ORDER_BOOK');
