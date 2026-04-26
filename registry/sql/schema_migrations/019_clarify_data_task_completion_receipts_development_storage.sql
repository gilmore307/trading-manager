-- Clarify data task completion receipt storage across development and durable modes.
-- Target engine: PostgreSQL.

UPDATE trading_registry
SET
  payload = 'Task completion receipt produced after a trading-data task attempt to record status, evidence, output references, and failure details when applicable; stored under trading-data development storage during development and moved to durable trading-storage contracts later',
  note = 'cross-repository evidence concept; development receipts use TRADING_DATA_DEVELOPMENT_STORAGE_ROOT, while durable schema and storage location remain pending in storage/request/manifest contract work'
WHERE id = 'trm_ZG72CBDJ';
