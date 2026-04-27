-- Move calendar discovery ownership from trading-data to trading-execution.
-- Target engine: PostgreSQL.

UPDATE trading_registry
SET path = 'trading-execution/src/trading_execution/calendar_discovery',
    applies_to = 'trading-execution',
    artifact_sync_policy = 'sync_artifact',
    note = 'Execution-owned release-calendar discovery bundle for future/realtime macro publication scheduling; trading-data remains focused on historical data retrieval'
WHERE kind = 'data_bundle'
  AND key = 'CALENDAR_DISCOVERY';

UPDATE trading_registry
SET applies_to = REPLACE(applies_to, 'trading-data', 'trading-execution'),
    note = note || '; execution-owned calendar/source-of-truth surface for future/realtime scheduling'
WHERE kind = 'term'
  AND key IN ('FOMC_CALENDAR', 'OFFICIAL_MACRO_RELEASE_CALENDAR');

UPDATE trading_registry
SET applies_to = 'calendar_discovery',
    note = note || '; owned by trading-execution calendar_discovery, not trading-data historical loaders'
WHERE kind = 'data_kind'
  AND key IN ('ECONOMIC_RELEASE_CALENDAR', 'FOMC_MEETING', 'FOMC_MINUTES', 'FOMC_SEP', 'FOMC_STATEMENT');

UPDATE trading_registry
SET applies_to = 'calendar_discovery',
    note = note || '; release schedule discovery is owned by trading-execution while macro values stay in macro_data'
WHERE kind = 'data_kind'
  AND key = 'MACRO_RELEASE_CALENDAR';
