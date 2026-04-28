-- Merge OHLCV/count fields by semantic meaning, not by bar/liquidity usage.
-- The same open/high/low/close/volume/vwap/trade_count concepts are reused
-- across market bars, option bars, and trade-derived liquidity intervals.

DELETE FROM trading_registry
WHERE id IN (
  'fld_MKT003',
  'fld_MKT005',
  'fld_MKT006',
  'fld_MKT007',
  'fld_MKT008',
  'fld_MKT009',
  'fld_MKT010'
);

UPDATE trading_registry
SET key = 'OPEN_PRICE',
    applies_to = 'market_data_template;option_bar_template;market_liquidity_template',
    note = 'canonical open price for a bar or trade-derived interval'
WHERE id = 'fld_OPT015';

UPDATE trading_registry
SET key = 'HIGH_PRICE',
    applies_to = 'market_data_template;option_bar_template;market_liquidity_template',
    note = 'canonical high price for a bar or trade-derived interval'
WHERE id = 'fld_OPT016';

UPDATE trading_registry
SET key = 'LOW_PRICE',
    applies_to = 'market_data_template;option_bar_template;market_liquidity_template',
    note = 'canonical low price for a bar or trade-derived interval'
WHERE id = 'fld_OPT017';

UPDATE trading_registry
SET key = 'CLOSE_PRICE',
    applies_to = 'market_data_template;option_bar_template;market_liquidity_template',
    note = 'canonical close price for a bar or trade-derived interval'
WHERE id = 'fld_OPT018';

UPDATE trading_registry
SET key = 'VOLUME',
    applies_to = 'market_data_template;option_bar_template;market_liquidity_template',
    note = 'canonical traded volume for a bar or trade-derived interval'
WHERE id = 'fld_OPT019';

UPDATE trading_registry
SET key = 'VWAP',
    applies_to = 'market_data_template;option_bar_template;market_liquidity_template',
    note = 'canonical volume-weighted average price for a bar or trade-derived interval'
WHERE id = 'fld_OPT021';

UPDATE trading_registry
SET key = 'TRADE_COUNT',
    payload = 'trade_count',
    applies_to = 'market_data_template;option_bar_template;market_liquidity_template',
    note = 'canonical number of trades contributing to a bar or trade-derived interval'
WHERE id = 'fld_OPT020';
