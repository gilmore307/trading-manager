-- Register manager-driven historical data task workflow terms.
-- Target engine: PostgreSQL.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, note)
VALUES
  ('trm_MBKALOPT', 'term', 'HISTORICAL_DATA_ACQUISITION', 'text', 'Historical-only data acquisition scope for trading-data; realtime market data belongs to trading-execution unless later re-scoped by contract', NULL, 'trading-data', 'scope boundary term; prevents source connector scripts from drifting into realtime execution behavior'),
  ('trm_Q2QS7TC6', 'term', 'DATA_TASK_KEY_FILE', 'text', 'Manager-issued task key file containing all information required for trading-data to run a specified historical data acquisition script with specified parameters and destination expectations', NULL, 'trading-manager;trading-data;trading-storage', 'cross-repository request/control concept; exact schema remains pending in request contract work'),
  ('trm_ZG72CBDJ', 'term', 'DATA_TASK_COMPLETION_RECEIPT', 'text', 'Storage-resident completion receipt produced after a trading-data task attempt to record status, evidence, output references, and failure details when applicable', NULL, 'trading-data;trading-storage;trading-manager', 'cross-repository evidence concept; exact schema and storage location remain pending in storage/request/manifest contract work')
ON CONFLICT (id) DO UPDATE
SET
  kind = EXCLUDED.kind,
  key = EXCLUDED.key,
  payload_format = EXCLUDED.payload_format,
  payload = EXCLUDED.payload,
  path = EXCLUDED.path,
  applies_to = EXCLUDED.applies_to,
  note = EXCLUDED.note;
