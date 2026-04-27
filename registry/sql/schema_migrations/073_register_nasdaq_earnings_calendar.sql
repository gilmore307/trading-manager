-- Register Nasdaq earnings-calendar scheduling source in trading-execution.
-- Target engine: PostgreSQL.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  ('dki_EQEARNCAL', 'data_kind', 'EQUITY_EARNINGS_CALENDAR', 'text', 'equity_earnings_calendar', 'https://www.nasdaq.com/market-activity/earnings', 'calendar_discovery;trading-execution', 'sync_artifact', 'Upcoming equity earnings calendar rows for execution scheduling; Nasdaq is an explicitly approved market-calendar source, while final historical filing/financial evidence remains owned by trading-data SEC/company loaders'),
  ('trm_NSDQEARN', 'term', 'NASDAQ_EARNINGS_CALENDAR', 'text', 'nasdaq_earnings_calendar', 'trading-execution/src/trading_execution/calendar_discovery', 'calendar_discovery;equity_earnings_calendar', 'sync_artifact', 'Nasdaq earnings calendar API/page adapter used to schedule future earnings-release monitoring; release phase is approximate, not audited filing evidence')
ON CONFLICT (id) DO UPDATE
SET kind = EXCLUDED.kind,
    key = EXCLUDED.key,
    payload_format = EXCLUDED.payload_format,
    payload = EXCLUDED.payload,
    path = EXCLUDED.path,
    applies_to = EXCLUDED.applies_to,
    artifact_sync_policy = EXCLUDED.artifact_sync_policy,
    note = EXCLUDED.note;
