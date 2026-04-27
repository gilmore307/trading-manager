-- Register ThetaData option final templates and their fields.
-- Target engine: PostgreSQL.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, note)
VALUES
  ('dki_OPCHAIN1', 'data_kind', 'OPTION_CHAIN_SNAPSHOT', 'text', 'option_chain_snapshot', 'trading-data/templates/data_kinds/thetadata/option_chain_snapshot.preview.json', 'thetadata_option_selection_snapshot', 'Complete nested ThetaData option-chain snapshot for one underlying/snapshot request; stores all visible unexpired contracts without liquidity/selection filtering'),
  ('dki_OPBAR001', 'data_kind', 'OPTION_BAR', 'text', 'option_bar', 'trading-data/templates/data_kinds/thetadata/option_bar.preview.csv', 'thetadata_option_primary_tracking', 'Final specified-contract option bar aggregated to task-key timeframe from transient ThetaData 1Sec OHLC source rows'),
  ('dki_OPEVENT1', 'data_kind', 'OPTION_ACTIVITY_EVENT', 'text', 'option_activity_event', 'trading-data/templates/data_kinds/thetadata/option_activity_event.preview.csv', 'thetadata_option_event_timeline', 'Final news-like option activity event row; event_text is human headline and structured fields carry model-readable metrics')
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
  note = note || '; source input only unless a later migration accepts this raw kind as final saved output'
WHERE kind = 'data_kind'
  AND key IN ('OPTION_TRADE', 'OPTION_TEMPLATE_QUOTE', 'OPTION_NBBO')
  AND path IS NOT NULL;

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, note)
VALUES
  ('fld_OPT001', 'field', 'OPTION_UNDERLYING', 'field_name', 'underlying', 'trading-data/templates/data_kinds/thetadata/README.md', 'option_template', 'underlying equity symbol for ThetaData option templates'),
  ('fld_OPT002', 'field', 'OPTION_EXPIRATION', 'field_name', 'expiration', 'trading-data/templates/data_kinds/thetadata/README.md', 'option_template', 'option contract expiration date'),
  ('fld_OPT003', 'field', 'OPTION_RIGHT', 'field_name', 'right', 'trading-data/templates/data_kinds/thetadata/README.md', 'option_template', 'option contract right CALL or PUT'),
  ('fld_OPT004', 'field', 'OPTION_STRIKE', 'field_name', 'strike', 'trading-data/templates/data_kinds/thetadata/README.md', 'option_template', 'option contract strike price'),
  ('fld_OPT005', 'field', 'OPTION_SNAPSHOT_TIME_ET', 'field_name', 'snapshot_time_et', 'trading-data/templates/data_kinds/thetadata/option_chain_snapshot.preview.json', 'option_chain_snapshot_template', 'point-in-time snapshot context timestamp in America/New_York'),
  ('fld_OPT006', 'field', 'OPTION_CONTRACT_COUNT', 'field_name', 'contract_count', 'trading-data/templates/data_kinds/thetadata/option_chain_snapshot.preview.json', 'option_chain_snapshot_template', 'number of contracts included in a nested option chain snapshot'),
  ('fld_OPT007', 'field', 'OPTION_CONTRACTS', 'field_name', 'contracts', 'trading-data/templates/data_kinds/thetadata/option_chain_snapshot.preview.json', 'option_chain_snapshot_template', 'array of visible unexpired option contracts in a chain snapshot'),
  ('fld_OPT008', 'field', 'OPTION_TEMPLATE_QUOTE', 'field_name', 'quote', 'trading-data/templates/data_kinds/thetadata/option_chain_snapshot.preview.json', 'option_chain_snapshot_template', 'nested quote object for one option contract'),
  ('fld_OPT009', 'field', 'OPTION_TEMPLATE_IV', 'field_name', 'iv', 'trading-data/templates/data_kinds/thetadata/option_chain_snapshot.preview.json', 'option_chain_snapshot_template', 'nested implied-volatility object for one option contract'),
  ('fld_OPT010', 'field', 'OPTION_TEMPLATE_GREEKS', 'field_name', 'greeks', 'trading-data/templates/data_kinds/thetadata/option_chain_snapshot.preview.json', 'option_chain_snapshot_template', 'nested first-order Greeks object for one option contract'),
  ('fld_OPT011', 'field', 'OPTION_UNDERLYING_CONTEXT', 'field_name', 'underlying', 'trading-data/templates/data_kinds/thetadata/option_chain_snapshot.preview.json', 'option_chain_snapshot_template', 'nested underlying price/timestamp context for one option contract'),
  ('fld_OPT012', 'field', 'OPTION_TEMPLATE_DERIVED', 'field_name', 'derived', 'trading-data/templates/data_kinds/thetadata/option_chain_snapshot.preview.json', 'option_chain_snapshot_template', 'nested derived fields for one option contract'),
  ('fld_OPT013', 'field', 'OPTION_TIMESTAMP_ET', 'field_name', 'timestamp_et', 'trading-data/templates/data_kinds/thetadata/option_bar.preview.csv', 'option_bar_template', 'option bar timestamp in America/New_York'),
  ('fld_OPT014', 'field', 'OPTION_TIMEFRAME', 'field_name', 'timeframe', 'trading-data/templates/data_kinds/thetadata/README.md', 'option_template', 'task-key requested output grain such as 1Min or 30Min'),
  ('fld_OPT015', 'field', 'OPTION_BAR_OPEN', 'field_name', 'open', 'trading-data/templates/data_kinds/thetadata/option_bar.preview.csv', 'option_bar_template', 'option bar open price'),
  ('fld_OPT016', 'field', 'OPTION_BAR_HIGH', 'field_name', 'high', 'trading-data/templates/data_kinds/thetadata/option_bar.preview.csv', 'option_bar_template', 'option bar high price'),
  ('fld_OPT017', 'field', 'OPTION_BAR_LOW', 'field_name', 'low', 'trading-data/templates/data_kinds/thetadata/option_bar.preview.csv', 'option_bar_template', 'option bar low price'),
  ('fld_OPT018', 'field', 'OPTION_BAR_CLOSE', 'field_name', 'close', 'trading-data/templates/data_kinds/thetadata/option_bar.preview.csv', 'option_bar_template', 'option bar close price'),
  ('fld_OPT019', 'field', 'OPTION_BAR_VOLUME', 'field_name', 'volume', 'trading-data/templates/data_kinds/thetadata/option_bar.preview.csv', 'option_bar_template', 'option bar contract volume'),
  ('fld_OPT020', 'field', 'OPTION_BAR_COUNT', 'field_name', 'count', 'trading-data/templates/data_kinds/thetadata/option_bar.preview.csv', 'option_bar_template', 'option bar trade count'),
  ('fld_OPT021', 'field', 'OPTION_BAR_VWAP', 'field_name', 'vwap', 'trading-data/templates/data_kinds/thetadata/option_bar.preview.csv', 'option_bar_template', 'option bar volume-weighted average price'),
  ('fld_OPT022', 'field', 'OPTION_EVENT_TIME_ET', 'field_name', 'event_time_et', 'trading-data/templates/data_kinds/thetadata/option_activity_event.preview.csv', 'option_activity_event_template', 'event source timestamp in America/New_York'),
  ('fld_OPT023', 'field', 'OPTION_DETECTION_TIME_ET', 'field_name', 'detection_time_et', 'trading-data/templates/data_kinds/thetadata/option_activity_event.preview.csv', 'option_activity_event_template', 'time the event is detected/reported in America/New_York'),
  ('fld_OPT024', 'field', 'OPTION_WINDOW_START_ET', 'field_name', 'window_start_et', 'trading-data/templates/data_kinds/thetadata/option_activity_event.preview.csv', 'option_activity_event_template', 'event rolling/window start timestamp in America/New_York'),
  ('fld_OPT025', 'field', 'OPTION_WINDOW_END_ET', 'field_name', 'window_end_et', 'trading-data/templates/data_kinds/thetadata/option_activity_event.preview.csv', 'option_activity_event_template', 'event rolling/window end timestamp in America/New_York'),
  ('fld_OPT026', 'field', 'OPTION_EVENT_SCORE', 'field_name', 'event_score', 'trading-data/templates/data_kinds/thetadata/option_activity_event.preview.csv', 'option_activity_event_template', 'human-reviewed initial option activity event score from triggered abnormal indicators'),
  ('fld_OPT027', 'field', 'OPTION_EVENT_FLAGS', 'field_name', 'event_flags', 'trading-data/templates/data_kinds/thetadata/option_activity_event.preview.csv', 'option_activity_event_template', 'semicolon-separated triggered option event indicators'),
  ('fld_OPT028', 'field', 'OPTION_EVENT_TEXT', 'field_name', 'event_text', 'trading-data/templates/data_kinds/thetadata/option_activity_event.preview.csv', 'option_activity_event_template', 'human-facing news-style headline mentioning only triggered abnormal indicators'),
  ('fld_OPT029', 'field', 'OPTION_EVENT_PRICE', 'field_name', 'price', 'trading-data/templates/data_kinds/thetadata/option_activity_event.preview.csv', 'option_activity_event_template', 'option event trade price'),
  ('fld_OPT030', 'field', 'OPTION_EVENT_SIZE', 'field_name', 'size', 'trading-data/templates/data_kinds/thetadata/option_activity_event.preview.csv', 'option_activity_event_template', 'option event trade size'),
  ('fld_OPT031', 'field', 'OPTION_EVENT_NOTIONAL', 'field_name', 'notional', 'trading-data/templates/data_kinds/thetadata/option_activity_event.preview.csv', 'option_activity_event_template', 'option event trade notional'),
  ('fld_OPT032', 'field', 'OPTION_TEMPLATE_BID', 'field_name', 'bid', 'trading-data/templates/data_kinds/thetadata/README.md', 'option_template', 'option bid price'),
  ('fld_OPT033', 'field', 'OPTION_TEMPLATE_ASK', 'field_name', 'ask', 'trading-data/templates/data_kinds/thetadata/README.md', 'option_template', 'option ask price'),
  ('fld_OPT034', 'field', 'OPTION_TEMPLATE_MID', 'field_name', 'mid', 'trading-data/templates/data_kinds/thetadata/README.md', 'option_template', 'option midpoint price'),
  ('fld_OPT035', 'field', 'OPTION_TEMPLATE_SPREAD', 'field_name', 'spread', 'trading-data/templates/data_kinds/thetadata/README.md', 'option_template', 'option ask minus bid spread'),
  ('fld_OPT036', 'field', 'OPTION_TEMPLATE_SPREAD_PCT', 'field_name', 'spread_pct', 'trading-data/templates/data_kinds/thetadata/README.md', 'option_template', 'option spread divided by midpoint'),
  ('fld_OPT037', 'field', 'OPTION_TEMPLATE_BID_SIZE', 'field_name', 'bid_size', 'trading-data/templates/data_kinds/thetadata/README.md', 'option_template', 'option bid size'),
  ('fld_OPT038', 'field', 'OPTION_TEMPLATE_ASK_SIZE', 'field_name', 'ask_size', 'trading-data/templates/data_kinds/thetadata/README.md', 'option_template', 'option ask size'),
  ('fld_OPT039', 'field', 'OPTION_QUOTE_TIMESTAMP_ET', 'field_name', 'quote_timestamp_et', 'trading-data/templates/data_kinds/thetadata/option_activity_event.preview.csv', 'option_activity_event_template', 'quote timestamp aligned to an option activity event'),
  ('fld_OPT040', 'field', 'OPTION_TRADE_EXCHANGE', 'field_name', 'trade_exchange', 'trading-data/templates/data_kinds/thetadata/option_activity_event.preview.csv', 'option_activity_event_template', 'ThetaData trade exchange code for option activity event'),
  ('fld_OPT041', 'field', 'OPTION_EVENT_SEQUENCE', 'field_name', 'sequence', 'trading-data/templates/data_kinds/thetadata/option_activity_event.preview.csv', 'option_activity_event_template', 'ThetaData sequence value for option activity event'),
  ('fld_OPT042', 'field', 'OPTION_EVENT_CONDITION', 'field_name', 'condition', 'trading-data/templates/data_kinds/thetadata/option_activity_event.preview.csv', 'option_activity_event_template', 'ThetaData trade condition code for option activity event'),
  ('fld_OPT043', 'field', 'OPTION_CUMULATIVE_TRADE_COUNT', 'field_name', 'cumulative_trade_count', 'trading-data/templates/data_kinds/thetadata/option_activity_event.preview.csv', 'option_activity_event_template', 'trade count accumulated in current event window up to detection time'),
  ('fld_OPT044', 'field', 'OPTION_CUMULATIVE_NOTIONAL', 'field_name', 'cumulative_notional', 'trading-data/templates/data_kinds/thetadata/option_activity_event.preview.csv', 'option_activity_event_template', 'trade notional accumulated in current event window up to detection time'),
  ('fld_OPT045', 'field', 'OPTION_TEMPLATE_IMPLIED_VOL', 'field_name', 'implied_vol', 'trading-data/templates/data_kinds/thetadata/README.md', 'option_template', 'option implied volatility'),
  ('fld_OPT046', 'field', 'OPTION_IV_ZSCORE_BY_EXPIRATION', 'field_name', 'iv_zscore_by_expiration', 'trading-data/templates/data_kinds/thetadata/option_activity_event.preview.csv', 'option_activity_event_template', 'cross-sectional IV z-score within expiration chain'),
  ('fld_OPT047', 'field', 'OPTION_IV_PERCENTILE_BY_EXPIRATION', 'field_name', 'iv_percentile_by_expiration', 'trading-data/templates/data_kinds/thetadata/option_activity_event.preview.csv', 'option_activity_event_template', 'cross-sectional IV percentile within expiration chain'),
  ('fld_OPT048', 'field', 'OPTION_PREVIOUS_IMPLIED_VOL', 'field_name', 'previous_implied_vol', 'trading-data/templates/data_kinds/thetadata/option_activity_event.preview.csv', 'option_activity_event_template', 'previous snapshot/window implied volatility used for IV jump detection'),
  ('fld_OPT049', 'field', 'OPTION_IV_CHANGE', 'field_name', 'iv_change', 'trading-data/templates/data_kinds/thetadata/option_activity_event.preview.csv', 'option_activity_event_template', 'absolute implied volatility change versus previous snapshot/window'),
  ('fld_OPT050', 'field', 'OPTION_IV_CHANGE_PCT', 'field_name', 'iv_change_pct', 'trading-data/templates/data_kinds/thetadata/option_activity_event.preview.csv', 'option_activity_event_template', 'relative implied volatility change versus previous snapshot/window'),
  ('fld_OPT051', 'field', 'OPTION_TEMPLATE_DELTA', 'field_name', 'delta', 'trading-data/templates/data_kinds/thetadata/README.md', 'option_template', 'option first-order Greek delta'),
  ('fld_OPT052', 'field', 'OPTION_TEMPLATE_THETA', 'field_name', 'theta', 'trading-data/templates/data_kinds/thetadata/README.md', 'option_template', 'option first-order Greek theta'),
  ('fld_OPT053', 'field', 'OPTION_TEMPLATE_VEGA', 'field_name', 'vega', 'trading-data/templates/data_kinds/thetadata/README.md', 'option_template', 'option first-order Greek vega'),
  ('fld_OPT054', 'field', 'OPTION_TEMPLATE_RHO', 'field_name', 'rho', 'trading-data/templates/data_kinds/thetadata/README.md', 'option_template', 'option first-order Greek rho'),
  ('fld_OPT055', 'field', 'OPTION_TEMPLATE_EPSILON', 'field_name', 'epsilon', 'trading-data/templates/data_kinds/thetadata/README.md', 'option_template', 'option first-order Greek epsilon'),
  ('fld_OPT056', 'field', 'OPTION_TEMPLATE_LAMBDA', 'field_name', 'lambda', 'trading-data/templates/data_kinds/thetadata/README.md', 'option_template', 'option first-order Greek lambda'),
  ('fld_OPT057', 'field', 'OPTION_TEMPLATE_UNDERLYING_PRICE', 'field_name', 'underlying_price', 'trading-data/templates/data_kinds/thetadata/README.md', 'option_template', 'underlying price associated with option IV/Greeks context'),
  ('fld_OPT058', 'field', 'OPTION_UNDERLYING_TIMESTAMP_ET', 'field_name', 'underlying_timestamp_et', 'trading-data/templates/data_kinds/thetadata/option_chain_snapshot.preview.json', 'option_chain_snapshot_template', 'underlying price timestamp in America/New_York'),
  ('fld_OPT059', 'field', 'OPTION_DAYS_TO_EXPIRATION', 'field_name', 'days_to_expiration', 'trading-data/templates/data_kinds/thetadata/option_chain_snapshot.preview.json', 'option_chain_snapshot_template', 'derived days to expiration for an option contract')
ON CONFLICT (id) DO UPDATE
SET
  kind = EXCLUDED.kind,
  key = EXCLUDED.key,
  payload_format = EXCLUDED.payload_format,
  payload = EXCLUDED.payload,
  path = EXCLUDED.path,
  applies_to = EXCLUDED.applies_to,
  note = EXCLUDED.note;
