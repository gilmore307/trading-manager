-- Apply generic field naming rule: reusable metrics use broad category keys;
-- scenario-specific prefixes remain only for scenario-specific meanings.
-- Target engine: PostgreSQL.

-- Reusable quote leaves.
UPDATE trading_registry SET key = 'QUOTE_BID', note = 'bid price in quote contexts'
WHERE kind = 'field' AND key = 'OPTION_TEMPLATE_BID';
UPDATE trading_registry SET key = 'QUOTE_ASK', note = 'ask price in quote contexts'
WHERE kind = 'field' AND key = 'OPTION_TEMPLATE_ASK';
UPDATE trading_registry SET key = 'QUOTE_MID', note = 'quote midpoint price in quote contexts'
WHERE kind = 'field' AND key = 'OPTION_TEMPLATE_MID';
UPDATE trading_registry SET key = 'QUOTE_SPREAD', note = 'ask minus bid spread in quote contexts'
WHERE kind = 'field' AND key = 'OPTION_TEMPLATE_SPREAD';
UPDATE trading_registry SET key = 'QUOTE_BID_SIZE', applies_to = 'option_template;option_chain_snapshot_template', note = 'bid size in quote contexts'
WHERE kind = 'field' AND key = 'OPTION_TEMPLATE_BID_SIZE';
UPDATE trading_registry SET key = 'QUOTE_ASK_SIZE', applies_to = 'option_template;option_chain_snapshot_template', note = 'ask size in quote contexts'
WHERE kind = 'field' AND key = 'OPTION_TEMPLATE_ASK_SIZE';
UPDATE trading_registry SET key = 'QUOTE_SPREAD_PCT', applies_to = 'option_template;option_chain_snapshot_template', note = 'quote spread divided by midpoint in quote contexts'
WHERE kind = 'field' AND key = 'OPTION_TEMPLATE_SPREAD_PCT';
UPDATE trading_registry SET key = 'QUOTE_BID_EXCHANGE', note = 'bid exchange code in nested quote context'
WHERE kind = 'field' AND key = 'OPTION_QUOTE_BID_EXCHANGE';
UPDATE trading_registry SET key = 'QUOTE_ASK_EXCHANGE', note = 'ask exchange code in nested quote context'
WHERE kind = 'field' AND key = 'OPTION_QUOTE_ASK_EXCHANGE';
UPDATE trading_registry SET key = 'QUOTE_BID_CONDITION', note = 'bid condition code in nested quote context'
WHERE kind = 'field' AND key = 'OPTION_QUOTE_BID_CONDITION';
UPDATE trading_registry SET key = 'QUOTE_ASK_CONDITION', note = 'ask condition code in nested quote context'
WHERE kind = 'field' AND key = 'OPTION_QUOTE_ASK_CONDITION';

-- Reusable trade leaves.
UPDATE trading_registry SET key = 'TRADE_PRICE', note = 'trade price value used in event-local or trade contexts'
WHERE kind = 'field' AND key = 'OPTION_EVENT_DETAIL_TRADE_PRICE';
UPDATE trading_registry SET key = 'TRADE_SIZE', note = 'trade size value used in event-local or trade contexts'
WHERE kind = 'field' AND key = 'OPTION_EVENT_DETAIL_TRADE_SIZE';
UPDATE trading_registry SET key = 'TRADE_TIMESTAMP_ET', note = 'trade timestamp in America/New_York used in event-local or trade contexts'
WHERE kind = 'field' AND key = 'OPTION_EVENT_DETAIL_TRADE_TIMESTAMP_ET';

-- Reusable option/IV/Greek leaves.
UPDATE trading_registry SET key = 'IMPLIED_VOL', note = 'implied volatility value used in option snapshots and event detail contexts'
WHERE kind = 'field' AND key = 'OPTION_TEMPLATE_IMPLIED_VOL';
UPDATE trading_registry SET key = 'IV_ERROR', note = 'ThetaData implied-volatility error/status value in nested IV context'
WHERE kind = 'field' AND key = 'OPTION_IV_ERROR';
UPDATE trading_registry SET key = 'IV_CONTEXT', note = 'nested implied-volatility context object'
WHERE kind = 'field' AND key = 'OPTION_TEMPLATE_IV';
UPDATE trading_registry SET key = 'OPTION_EVENT_DETAIL_IV_CONTEXT', note = 'nested implied-volatility context near the triggering option activity event'
WHERE kind = 'field' AND key = 'OPTION_EVENT_DETAIL_IV_CONTEXT';
UPDATE trading_registry SET key = 'IV_PERCENTILE_BY_EXPIRATION', note = 'cross-sectional implied-volatility percentile within the option expiration'
WHERE kind = 'field' AND key = 'OPTION_EVENT_DETAIL_IV_PERCENTILE_BY_EXPIRATION';
UPDATE trading_registry SET key = 'IV_RANK_IN_EXPIRATION', note = 'rank of contract implied volatility within its expiration cross-section'
WHERE kind = 'field' AND key = 'OPTION_EVENT_DETAIL_IV_RANK_IN_EXPIRATION';
UPDATE trading_registry SET key = 'IV_ZSCORE_BY_EXPIRATION', note = 'z-score of contract implied volatility within its expiration cross-section'
WHERE kind = 'field' AND key = 'OPTION_EVENT_DETAIL_IV_ZSCORE_BY_EXPIRATION';

UPDATE trading_registry SET key = 'GREEKS_CONTEXT', note = 'nested option Greeks context object'
WHERE kind = 'field' AND key = 'OPTION_TEMPLATE_GREEKS';
UPDATE trading_registry SET key = 'GREEK_DELTA', note = 'option first-order Greek delta'
WHERE kind = 'field' AND key = 'OPTION_TEMPLATE_DELTA';
UPDATE trading_registry SET key = 'GREEK_THETA', note = 'option first-order Greek theta'
WHERE kind = 'field' AND key = 'OPTION_TEMPLATE_THETA';
UPDATE trading_registry SET key = 'GREEK_VEGA', note = 'option first-order Greek vega'
WHERE kind = 'field' AND key = 'OPTION_TEMPLATE_VEGA';
UPDATE trading_registry SET key = 'GREEK_RHO', note = 'option first-order Greek rho'
WHERE kind = 'field' AND key = 'OPTION_TEMPLATE_RHO';
UPDATE trading_registry SET key = 'GREEK_EPSILON', note = 'option first-order Greek epsilon'
WHERE kind = 'field' AND key = 'OPTION_TEMPLATE_EPSILON';
UPDATE trading_registry SET key = 'GREEK_LAMBDA', note = 'option first-order Greek lambda'
WHERE kind = 'field' AND key = 'OPTION_TEMPLATE_LAMBDA';

-- Reusable option snapshot/context fields.
UPDATE trading_registry SET key = 'OPTION_QUOTE_CONTEXT', note = 'nested option quote context object'
WHERE kind = 'field' AND key = 'OPTION_TEMPLATE_QUOTE';
UPDATE trading_registry SET key = 'DERIVED_CONTEXT', note = 'nested derived field context object'
WHERE kind = 'field' AND key = 'OPTION_TEMPLATE_DERIVED';
UPDATE trading_registry SET key = 'SNAPSHOT_TIME_ET', note = 'point-in-time snapshot context timestamp in America/New_York'
WHERE kind = 'field' AND key = 'OPTION_SNAPSHOT_TIME_ET';
UPDATE trading_registry SET key = 'BAR_COUNT', note = 'bar trade/count value when source exposes count rather than trade_count'
WHERE kind = 'field' AND key = 'OPTION_BAR_COUNT';
UPDATE trading_registry SET key = 'UNDERLYING_PRICE', note = 'underlying price associated with an option or model context'
WHERE kind = 'field' AND key = 'OPTION_TEMPLATE_UNDERLYING_PRICE';
UPDATE trading_registry SET key = 'UNDERLYING_TIMESTAMP_ET', note = 'underlying price timestamp in America/New_York'
WHERE kind = 'field' AND key = 'OPTION_UNDERLYING_TIMESTAMP_ET';
UPDATE trading_registry SET key = 'OPTION_CONTRACT_SYMBOL', note = 'human-readable option contract symbol'
WHERE kind = 'field' AND key = 'OPTION_EVENT_DETAIL_CONTRACT_SYMBOL';

-- Reusable event/model statistics that are not specific to option event detail.
UPDATE trading_registry SET key = 'EXPIRATION_CHAIN_CONTRACT_COUNT', note = 'number of contracts in the expiration cross-section used for option context'
WHERE kind = 'field' AND key = 'OPTION_EVENT_DETAIL_EXPIRATION_CHAIN_CONTRACT_COUNT';
UPDATE trading_registry SET key = 'CONTRACT_PRIOR_WINDOW_VOLUME', note = 'observed contract volume in the immediately comparable prior evidence window'
WHERE kind = 'field' AND key = 'OPTION_EVENT_DETAIL_CONTRACT_PRIOR_WINDOW_VOLUME';
UPDATE trading_registry SET key = 'VOLUME_VS_PRIOR_WINDOW_RATIO', note = 'observed current-window volume divided by comparable prior-window volume when defined'
WHERE kind = 'field' AND key = 'OPTION_EVENT_DETAIL_VOLUME_VS_PRIOR_WINDOW_RATIO';
UPDATE trading_registry SET key = 'VOLUME_PERCENTILE_20D_SAME_TIME', note = 'observed percentile of current-window volume versus the last 20 comparable same-time windows'
WHERE kind = 'field' AND key = 'OPTION_EVENT_DETAIL_VOLUME_PERCENTILE_20D_SAME_TIME';
UPDATE trading_registry SET key = 'WINDOW_TRADE_COUNT', note = 'trade count accumulated in an evidence window'
WHERE kind = 'field' AND key = 'OPTION_EVENT_DETAIL_WINDOW_TRADE_COUNT';
UPDATE trading_registry SET key = 'WINDOW_VOLUME', note = 'contract or unit volume accumulated in an evidence window'
WHERE kind = 'field' AND key = 'OPTION_EVENT_DETAIL_WINDOW_VOLUME';
UPDATE trading_registry SET key = 'WINDOW_NOTIONAL', note = 'notional value accumulated in an evidence window'
WHERE kind = 'field' AND key = 'OPTION_EVENT_DETAIL_WINDOW_NOTIONAL';
UPDATE trading_registry SET key = 'WINDOW_START_ET', note = 'evidence window start timestamp in America/New_York'
WHERE kind = 'field' AND key = 'OPTION_EVENT_DETAIL_WINDOW_START_ET';
UPDATE trading_registry SET key = 'WINDOW_END_ET', note = 'evidence window end timestamp in America/New_York'
WHERE kind = 'field' AND key = 'OPTION_EVENT_DETAIL_WINDOW_END_ET';
UPDATE trading_registry SET key = 'FIRST_SEEN_IN_WINDOW', note = 'boolean metric indicating first appearance or first trade in the current evidence window'
WHERE kind = 'field' AND key = 'OPTION_EVENT_DETAIL_FIRST_SEEN_IN_WINDOW';

-- Keep scenario-specific option event detail prefixes for fields whose semantics are event-specific.
UPDATE trading_registry SET note = 'triggering trade price minus contemporaneous ask metric used to identify ask-side option activity'
WHERE kind = 'field' AND key = 'OPTION_EVENT_DETAIL_PRICE_VS_ASK';
UPDATE trading_registry SET note = 'observed ratio/indicator showing how closely the triggering trade touched the contemporaneous ask in an option activity event'
WHERE kind = 'field' AND key = 'OPTION_EVENT_DETAIL_ASK_TOUCH_RATIO';
