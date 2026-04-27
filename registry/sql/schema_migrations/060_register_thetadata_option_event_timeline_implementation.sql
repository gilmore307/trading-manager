-- Register implemented ThetaData option event timeline bundle path.
-- Target engine: PostgreSQL.

UPDATE trading_registry
SET path = 'trading-data/src/trading_data/data_sources/thetadata_option_event_timeline',
    artifact_sync_policy = 'sync_artifact',
    note = 'Implemented ThetaData option bundle for event-only option activity timeline rows; caller supplies contract, evidence-window timeframe, and task/model current_standard; transient trade_quote rows emit final option_activity_event CSV plus per-event detail JSON artifacts'
WHERE kind = 'data_bundle'
  AND key = 'THETADATA_OPTION_EVENT_TIMELINE';
