-- Prefix bar OHLCV/count registry fields so broad names do not collide with
-- quote, trade, option, or underlying contexts. Keep timeframe generic.

UPDATE trading_registry
SET key = 'TIMEFRAME',
    payload = 'timeframe',
    note = 'requested or output time grain such as 1Min, 30Min, or 1Day'
WHERE key = 'DATA_TIMEFRAME';

UPDATE trading_registry
SET key = 'BAR_OPEN',
    payload = 'bar_open',
    note = 'bar open price'
WHERE key = 'OPEN_PRICE';

UPDATE trading_registry
SET key = 'BAR_HIGH',
    payload = 'bar_high',
    note = 'bar high price'
WHERE key = 'HIGH_PRICE';

UPDATE trading_registry
SET key = 'BAR_LOW',
    payload = 'bar_low',
    note = 'bar low price'
WHERE key = 'LOW_PRICE';

UPDATE trading_registry
SET key = 'BAR_CLOSE',
    payload = 'bar_close',
    note = 'bar close price'
WHERE key = 'CLOSE_PRICE';

UPDATE trading_registry
SET key = 'BAR_VOLUME',
    payload = 'bar_volume',
    note = 'bar traded volume'
WHERE key = 'VOLUME';

UPDATE trading_registry
SET key = 'BAR_VWAP',
    payload = 'bar_vwap',
    note = 'bar volume-weighted average price'
WHERE key = 'VWAP';

UPDATE trading_registry
SET key = 'BAR_TRADE_COUNT',
    payload = 'bar_trade_count',
    note = 'number of trades contributing to a bar'
WHERE key = 'TRADE_COUNT';
