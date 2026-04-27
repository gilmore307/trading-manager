-- Remove ambiguous threshold wording from current option event registry notes.
-- Target engine: PostgreSQL.

UPDATE trading_registry
SET
  note = 'event-time standard produced by the detection model for one triggered indicator type; not a global fixed rule value and may change across model versions/runs'
WHERE kind = 'field'
  AND key = 'OPTION_EVENT_DETAIL_CURRENT_STANDARD';

UPDATE trading_registry
SET
  note = 'short human-readable event/news summary; for option_activity_event this must contain only abnormal indicator type names and must not include normal metrics, trigger values, current_standard values, or scoring values'
WHERE kind = 'field'
  AND key = 'TIMELINE_SUMMARY';
