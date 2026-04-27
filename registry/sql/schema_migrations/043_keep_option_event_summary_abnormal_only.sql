-- Clarify that option activity event summary carries only abnormal indicators.
-- Target engine: PostgreSQL.

UPDATE trading_registry
SET
  note = 'Final news-like option activity event row using the shared event/news timeline fields; headline is human-facing, summary carries only triggered abnormal indicators, and scoring/normal metrics belong to downstream models'
WHERE kind = 'data_kind'
  AND key = 'OPTION_ACTIVITY_EVENT';

UPDATE trading_registry
SET
  note = 'short human-readable event/news summary; for option_activity_event this must contain only triggered abnormal indicators and must not include normal metrics or scoring values'
WHERE kind = 'field'
  AND key = 'TIMELINE_SUMMARY';
