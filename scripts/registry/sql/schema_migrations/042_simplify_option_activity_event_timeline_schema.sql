-- Simplify option_activity_event to the shared news/timeline field shape.
-- Target engine: PostgreSQL.

UPDATE trading_registry
SET
  note = 'Final news-like option activity event row using the shared event/news timeline fields; headline is human-facing, summary carries triggered abnormal indicators and compact nested context, and scoring belongs to downstream models'
WHERE kind = 'data_kind'
  AND key = 'OPTION_ACTIVITY_EVENT';

UPDATE trading_registry
SET
  note = 'short human-readable event/news summary; for option_activity_event this carries only triggered abnormal indicators and compact nested metric/context text, not normal metrics'
WHERE kind = 'field'
  AND key = 'TIMELINE_SUMMARY';

UPDATE trading_registry
SET
  note = 'semicolon-separated symbols or compact symbol/context entries associated with a news/event timeline row; for option_activity_event this may include underlying and contract context'
WHERE kind = 'field'
  AND key = 'TIMELINE_SYMBOLS';

UPDATE trading_registry
SET
  note = 'human-readable headline shared by news and event timeline outputs; for option_activity_event it should read like a news headline and mention only triggered abnormal indicators'
WHERE kind = 'field'
  AND key = 'TIMELINE_HEADLINE';

DELETE FROM trading_registry
WHERE kind = 'field'
  AND key IN (
    'OPTION_EVENT_TIME_ET',
    'OPTION_DETECTION_TIME_ET',
    'OPTION_WINDOW_START_ET',
    'OPTION_WINDOW_END_ET',
    'OPTION_EVENT_SCORE',
    'OPTION_EVENT_FLAGS',
    'OPTION_EVENT_TEXT',
    'OPTION_EVENT_PRICE',
    'OPTION_EVENT_SIZE',
    'OPTION_EVENT_NOTIONAL',
    'OPTION_QUOTE_TIMESTAMP_ET',
    'OPTION_TRADE_EXCHANGE',
    'OPTION_EVENT_SEQUENCE',
    'OPTION_EVENT_CONDITION',
    'OPTION_CUMULATIVE_TRADE_COUNT',
    'OPTION_CUMULATIVE_NOTIONAL',
    'OPTION_IV_ZSCORE_BY_EXPIRATION',
    'OPTION_IV_PERCENTILE_BY_EXPIRATION',
    'OPTION_PREVIOUS_IMPLIED_VOL',
    'OPTION_IV_CHANGE',
    'OPTION_IV_CHANGE_PCT'
  );
