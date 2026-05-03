-- Reframe ThetaData option acquisition around use-case bundles instead of endpoint families.
-- Target engine: PostgreSQL.

UPDATE trading_registry
SET
  key = 'THETADATA_OPTION_PRIMARY_TRACKING',
  payload = 'thetadata_option_primary_tracking',
  path = NULL,
  note = 'ThetaData option bundle for selecting and tracking one primary/main option contract alongside equity bars and liquidity at the same research grain'
WHERE id = 'dbu_9O1A3ATK'
  AND kind = 'data_bundle';

UPDATE trading_registry
SET
  key = 'THETADATA_OPTION_SELECTION_SNAPSHOT',
  payload = 'thetadata_option_selection_snapshot',
  path = NULL,
  note = 'ThetaData option bundle for point-in-time option-chain snapshots used to simulate contract selection from information visible at signal time'
WHERE id = 'dbu_GI7N2MIP'
  AND kind = 'data_bundle';

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, note)
VALUES
  ('dbu_Q5TXEVNT', 'data_bundle', 'THETADATA_OPTION_EVENT_TIMELINE', 'text', 'thetadata_option_event_timeline', NULL, 'trading-data', 'ThetaData option bundle for news-like event timeline records describing unusual option contract activity')
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
  applies_to = 'thetadata_option_primary_tracking;thetadata_option_selection_snapshot',
  note = 'ThetaData option contract/reference records used for primary-contract tracking and point-in-time selection snapshots'
WHERE kind = 'data_kind'
  AND key = 'OPTION_CONTRACT';

UPDATE trading_registry
SET
  applies_to = 'thetadata_option_primary_tracking',
  note = 'ThetaData option OHLC records for the selected primary/main contract tracked alongside equity bars'
WHERE kind = 'data_kind'
  AND key = 'OPTION_OHLC';

UPDATE trading_registry
SET
  applies_to = 'thetadata_option_primary_tracking;thetadata_option_selection_snapshot',
  note = 'ThetaData option end-of-day records used for primary-contract tracking and visible chain context when applicable'
WHERE kind = 'data_kind'
  AND key = 'OPTION_EOD';

UPDATE trading_registry
SET
  applies_to = 'thetadata_option_primary_tracking;thetadata_option_selection_snapshot',
  note = 'ThetaData option open interest records used for primary-contract tracking and point-in-time chain selection context'
WHERE kind = 'data_kind'
  AND key = 'OPTION_OPEN_INTEREST';

UPDATE trading_registry
SET
  applies_to = 'thetadata_option_primary_tracking;thetadata_option_selection_snapshot',
  note = 'ThetaData option implied volatility records used for primary-contract tracking and point-in-time chain selection context'
WHERE kind = 'data_kind'
  AND key = 'OPTION_IMPLIED_VOLATILITY';

UPDATE trading_registry
SET
  applies_to = 'thetadata_option_primary_tracking;thetadata_option_selection_snapshot',
  note = 'ThetaData first-order Greeks used for primary-contract tracking and point-in-time chain selection context'
WHERE kind = 'data_kind'
  AND key = 'OPTION_GREEKS_FIRST_ORDER';

UPDATE trading_registry
SET
  applies_to = 'thetadata_option_event_timeline;thetadata_option_primary_tracking',
  note = 'ThetaData option trades are source inputs for unusual-activity event timelines and primary-contract liquidity features; default final persistence should aggregate or eventize rather than save bulky raw trades'
WHERE kind = 'data_kind'
  AND key = 'OPTION_TRADE';

UPDATE trading_registry
SET
  applies_to = 'thetadata_option_event_timeline;thetadata_option_primary_tracking',
  note = 'ThetaData option quotes are source inputs for unusual-activity event timelines and primary-contract liquidity features; default final persistence should aggregate or eventize rather than save bulky raw quotes'
WHERE kind = 'data_kind'
  AND key = 'OPTION_QUOTE';

UPDATE trading_registry
SET
  applies_to = 'thetadata_option_event_timeline;thetadata_option_primary_tracking',
  note = 'ThetaData option trade-quote/NBBO rows align trades with quotes and are preferred source inputs for option liquidity and unusual-activity event timelines'
WHERE kind = 'data_kind'
  AND key = 'OPTION_NBBO';

UPDATE trading_registry
SET
  applies_to = 'thetadata_option_selection_snapshot',
  note = 'ThetaData requested-time option quote snapshot records for simulating visible chain information at signal/contract-selection time'
WHERE kind = 'data_kind'
  AND key = 'OPTION_SNAPSHOT';

UPDATE trading_registry
SET
  applies_to = 'thetadata_option_selection_snapshot',
  note = 'ThetaData second-order Greeks remain entitlement-blocked on the current STANDARD account; include only in point-in-time selection snapshots if entitlement is upgraded'
WHERE kind = 'data_kind'
  AND key = 'OPTION_GREEKS_SECOND_ORDER';

UPDATE trading_registry
SET
  applies_to = 'thetadata_option_selection_snapshot',
  note = 'ThetaData third-order Greeks remain entitlement-blocked on the current STANDARD account; include only in point-in-time selection snapshots if entitlement is upgraded'
WHERE kind = 'data_kind'
  AND key = 'OPTION_GREEKS_THIRD_ORDER';

UPDATE trading_registry
SET
  applies_to = 'thetadata_option_event_timeline',
  note = 'ThetaData trade Greeks remain entitlement-blocked on the current STANDARD account; event timeline may use them only if entitlement is upgraded'
WHERE kind = 'data_kind'
  AND key = 'OPTION_TRADE_GREEKS';
