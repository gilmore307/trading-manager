-- Make OKX crypto trades transient-only now that crypto_liquidity_bar owns final trade-derived features.
-- Target engine: PostgreSQL.

UPDATE trading_registry
SET
  path = NULL,
  applies_to = 'okx_crypto_market_data',
  note = 'OKX crypto trades are transient inputs for crypto_liquidity_bar, not default standalone final saved outputs; do not save crypto_trade.csv unless explicitly approved for a bounded debug/audit use case'
WHERE kind = 'data_kind'
  AND key = 'CRYPTO_TRADE';

UPDATE trading_registry
SET
  note = 'OKX crypto liquidity interval row is the accepted final trade-derived output; raw crypto trades are transient inputs and quote-derived fields may be null/blank when no sampled order-book snapshots exist'
WHERE kind = 'data_kind'
  AND key = 'CRYPTO_LIQUIDITY_BAR';
