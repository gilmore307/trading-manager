-- Generalize quote/trade field keys that are not option-event-specific.
-- Target engine: PostgreSQL.

-- Liquidity interval quote aggregates. These remain separate from point-in-time quote fields
-- because their payloads/semantics are average or last values over an interval.
UPDATE trading_registry SET key = 'QUOTE_AVG_ASK', note = 'average ask price in a liquidity interval'
WHERE kind = 'field' AND key = 'MARKET_AVG_ASK';
UPDATE trading_registry SET key = 'QUOTE_AVG_BID', note = 'average bid price in a liquidity interval'
WHERE kind = 'field' AND key = 'MARKET_AVG_BID';
UPDATE trading_registry SET key = 'QUOTE_AVG_MID', note = 'average quote midpoint price in a liquidity interval'
WHERE kind = 'field' AND key = 'MARKET_AVG_MID';
UPDATE trading_registry SET key = 'QUOTE_AVG_SPREAD', note = 'average bid-ask spread in a liquidity interval'
WHERE kind = 'field' AND key = 'MARKET_AVG_SPREAD';
UPDATE trading_registry SET key = 'QUOTE_LAST_ASK', note = 'last ask price observed in a liquidity interval'
WHERE kind = 'field' AND key = 'MARKET_LAST_ASK';
UPDATE trading_registry SET key = 'QUOTE_LAST_BID', note = 'last bid price observed in a liquidity interval'
WHERE kind = 'field' AND key = 'MARKET_LAST_BID';
UPDATE trading_registry SET key = 'QUOTE_LAST_MID', note = 'last quote midpoint price observed in a liquidity interval'
WHERE kind = 'field' AND key = 'MARKET_LAST_MID';
UPDATE trading_registry SET key = 'QUOTE_COUNT', note = 'number of quotes contributing to an interval; may be blank when quote history is unavailable'
WHERE kind = 'field' AND key = 'MARKET_QUOTE_COUNT';

-- Point-in-time quote context fields used by option activity details.
UPDATE trading_registry SET key = 'QUOTE_ASK', note = 'ask price in a point-in-time quote context'
WHERE kind = 'field' AND key = 'OPTION_EVENT_DETAIL_QUOTE_ASK';
UPDATE trading_registry SET key = 'QUOTE_BID', note = 'bid price in a point-in-time quote context'
WHERE kind = 'field' AND key = 'OPTION_EVENT_DETAIL_QUOTE_BID';
UPDATE trading_registry SET key = 'QUOTE_MID', note = 'quote midpoint price in a point-in-time quote context'
WHERE kind = 'field' AND key = 'OPTION_EVENT_DETAIL_QUOTE_MID';
UPDATE trading_registry SET key = 'QUOTE_SPREAD', note = 'ask minus bid spread in a point-in-time quote context'
WHERE kind = 'field' AND key = 'OPTION_EVENT_DETAIL_QUOTE_SPREAD';
UPDATE trading_registry SET key = 'QUOTE_TIMESTAMP_ET', note = 'quote timestamp in America/New_York for a point-in-time quote context'
WHERE kind = 'field' AND key = 'OPTION_EVENT_DETAIL_QUOTE_TIMESTAMP_ET';
UPDATE trading_registry SET key = 'QUOTE_CONTEXT', note = 'nested point-in-time quote context object'
WHERE kind = 'field' AND key = 'OPTION_EVENT_DETAIL_QUOTE_CONTEXT';
UPDATE trading_registry SET key = 'QUOTE_ASK_TOUCH_RATIO', note = 'observed ratio/indicator showing how closely a trade touched the contemporaneous ask'
WHERE kind = 'field' AND key = 'OPTION_EVENT_DETAIL_ASK_TOUCH_RATIO';

-- Trade fields and interval trade aggregates.
UPDATE trading_registry SET key = 'TRADE_PRICE', note = 'trade price value used in event-local or trade context'
WHERE kind = 'field' AND key = 'OPTION_EVENT_DETAIL_TRADE_PRICE';
UPDATE trading_registry SET key = 'TRADE_SIZE', note = 'trade size value used in event-local or trade context'
WHERE kind = 'field' AND key = 'OPTION_EVENT_DETAIL_TRADE_SIZE';
UPDATE trading_registry SET key = 'TRADE_TIMESTAMP_ET', note = 'trade timestamp in America/New_York used in event-local or trade context'
WHERE kind = 'field' AND key = 'OPTION_EVENT_DETAIL_TRADE_TIMESTAMP_ET';
UPDATE trading_registry SET key = 'TRADE_PRICE_VS_ASK', note = 'trade price minus contemporaneous ask metric used to identify ask-side activity'
WHERE kind = 'field' AND key = 'OPTION_EVENT_DETAIL_PRICE_VS_ASK';
UPDATE trading_registry SET key = 'TRADE_COUNT', note = 'number of trades contributing to a bar or liquidity interval'
WHERE kind = 'field' AND key = 'MARKET_TRADE_COUNT';
UPDATE trading_registry SET key = 'TRADE_VOLUME', note = 'trade volume contributing to a liquidity interval'
WHERE kind = 'field' AND key = 'MARKET_TRADE_VOLUME';
UPDATE trading_registry SET key = 'TRADE_VWAP', note = 'trade volume-weighted average price in a liquidity interval'
WHERE kind = 'field' AND key = 'MARKET_TRADE_VWAP';
UPDATE trading_registry SET key = 'TRADE_OPEN', note = 'first trade price in a liquidity interval'
WHERE kind = 'field' AND key = 'MARKET_TRADE_OPEN';
UPDATE trading_registry SET key = 'TRADE_HIGH', note = 'highest trade price in a liquidity interval'
WHERE kind = 'field' AND key = 'MARKET_TRADE_HIGH';
UPDATE trading_registry SET key = 'TRADE_LOW', note = 'lowest trade price in a liquidity interval'
WHERE kind = 'field' AND key = 'MARKET_TRADE_LOW';
UPDATE trading_registry SET key = 'TRADE_CLOSE', note = 'last trade price in a liquidity interval'
WHERE kind = 'field' AND key = 'MARKET_TRADE_CLOSE';
UPDATE trading_registry SET key = 'TRADE_VWAP_MINUS_QUOTE_AVG_MID', note = 'trade VWAP minus average quote midpoint in a liquidity interval'
WHERE kind = 'field' AND key = 'MARKET_VWAP_MINUS_AVG_MID';

-- Other generic market-data fields.
UPDATE trading_registry SET key = 'INSTRUMENT_SYMBOL', note = 'model-facing instrument symbol field shared by market outputs'
WHERE kind = 'field' AND key = 'MARKET_SYMBOL';
UPDATE trading_registry SET key = 'INTERVAL_START_ET', note = 'interval start timestamp in America/New_York for interval aggregate outputs'
WHERE kind = 'field' AND key = 'MARKET_INTERVAL_START_ET';
