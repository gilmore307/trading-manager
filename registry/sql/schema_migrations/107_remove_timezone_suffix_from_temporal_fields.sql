-- Temporal field payloads do not carry ET/UTC suffixes; the temporal_field
-- contract and template documentation own timezone semantics. Normalized final
-- outputs default to America/New_York unless a reviewed source contract says otherwise.

UPDATE trading_registry
SET key = 'DATA_TIMESTAMP',
    payload = 'timestamp',
    note = 'canonical timestamp shared by final bar outputs and nested quote/snapshot contexts. Temporal value format: ISO 8601; normalized final outputs use America/New_York semantics unless explicitly reviewed otherwise.'
WHERE id = 'fld_OPT013';

UPDATE trading_registry
SET key = 'EVENT_EFFECTIVE_TIME',
    payload = 'effective_time',
    note = 'earliest trading timestamp when the event is safely observable/actionable; required to prevent look-ahead leakage. Temporal value format: ISO 8601; normalized final outputs use America/New_York semantics unless explicitly reviewed otherwise.'
WHERE id = 'fld_EVT014';

UPDATE trading_registry
SET key = 'EVENT_FACTOR_AS_OF',
    payload = 'factor_as_of',
    note = 'timestamp when event factor values were generated or became available. Temporal value format: ISO 8601; normalized final outputs use America/New_York semantics unless explicitly reviewed otherwise.'
WHERE id = 'fld_EVT031';

UPDATE trading_registry
SET key = 'EVENT_TIME',
    payload = 'event_time',
    note = 'canonical source publication, detection, or calendar event timestamp normalized for model use. Temporal value format: ISO 8601; normalized final outputs use America/New_York semantics unless explicitly reviewed otherwise.'
WHERE id = 'fld_EVT013';

UPDATE trading_registry
SET key = 'GDELT_ARTICLE_SEEN_AT',
    payload = 'seen_at',
    note = 'GDELT article observation timestamp normalized for model use. Temporal value format: ISO 8601; normalized final outputs use America/New_York semantics unless explicitly reviewed otherwise.'
WHERE id = 'fld_GDLT002';

UPDATE trading_registry
SET key = 'GENERATED_AT',
    payload = 'generated_at',
    note = 'canonical timestamp when an analysis report, standard snapshot, or generated artifact was produced. Temporal value format: ISO 8601; normalized final outputs use America/New_York semantics unless explicitly reviewed otherwise.'
WHERE id = 'fld_EVT037';

UPDATE trading_registry
SET key = 'INTERVAL_START',
    payload = 'interval_start',
    note = 'interval start timestamp for interval aggregate outputs. Temporal value format: ISO 8601; normalized final outputs use America/New_York semantics unless explicitly reviewed otherwise.'
WHERE id = 'fld_MKT002';

UPDATE trading_registry
SET key = 'SNAPSHOT_TIME',
    payload = 'snapshot_time',
    note = 'point-in-time snapshot context timestamp. Temporal value format: ISO 8601; normalized final outputs use America/New_York semantics unless explicitly reviewed otherwise.'
WHERE id = 'fld_OPT005';

UPDATE trading_registry
SET key = 'STOCK_ETF_AVAILABLE_TIME',
    payload = 'available_time',
    note = 'earliest timestamp when this exposure row is available for model use. Temporal value format: ISO 8601; normalized final outputs use America/New_York semantics unless explicitly reviewed otherwise.'
WHERE id = 'fld_STKEX011';

UPDATE trading_registry
SET key = 'TRADE_TIMESTAMP',
    payload = 'trade_timestamp',
    note = 'trade timestamp used in event-local or trade contexts. Temporal value format: ISO 8601; normalized final outputs use America/New_York semantics unless explicitly reviewed otherwise.'
WHERE id = 'fld_OPD016';

UPDATE trading_registry
SET key = 'UNDERLYING_TIMESTAMP',
    payload = 'underlying_timestamp',
    note = 'underlying price timestamp. Temporal value format: ISO 8601; normalized final outputs use America/New_York semantics unless explicitly reviewed otherwise.'
WHERE id = 'fld_OPT058';

UPDATE trading_registry
SET key = 'WINDOW_END',
    payload = 'window_end',
    note = 'evidence window end timestamp. Temporal value format: ISO 8601; normalized final outputs use America/New_York semantics unless explicitly reviewed otherwise.'
WHERE id = 'fld_OPD007';

UPDATE trading_registry
SET key = 'WINDOW_START',
    payload = 'window_start',
    note = 'evidence window start timestamp. Temporal value format: ISO 8601; normalized final outputs use America/New_York semantics unless explicitly reviewed otherwise.'
WHERE id = 'fld_OPD006';
