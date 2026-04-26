-- Register data task run terminology and clarify stable task-key/run receipt split.
-- Target engine: PostgreSQL.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, note)
VALUES
  ('trm_TU2UWZK6', 'term', 'DATA_TASK_RUN', 'text', 'One invocation of a stable data task key, such as a scheduled or periodic run, with per-run status and output evidence stored in completion receipt runs entries', NULL, 'trading-data;trading-manager;trading-storage', 'task key stays stable; run-specific values belong in completion_receipt.runs[]')
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
SET note = 'minimal stable manager-issued historical data task key template; one task key may have many runs; include only fields used by manager handoff and bundle execution; not an accepted schema until contract review'
WHERE id = 'out_SGC6SHTM';

UPDATE trading_registry
SET note = 'minimal draft completion receipt template with runs[] for per-run evidence; include only fields used for run status, output references, row counts, and error evidence; durable receipt contract remains future work'
WHERE id = 'out_ERYNXVJ3';
