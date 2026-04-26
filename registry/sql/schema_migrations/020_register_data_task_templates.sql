-- Register reusable data task drafting templates.
-- Target engine: PostgreSQL.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, note)
VALUES
  ('out_SGC6SHTM', 'output', 'DATA_TASK_KEY_TEMPLATE', 'file', 'templates/data_tasks/task_key.json', '/root/projects/trading-main/templates/data_tasks/task_key.json', 'trading-manager;trading-data', 'draft manager-issued historical data task key template; not an accepted schema until contract review'),
  ('out_PH4FEKTH', 'output', 'DATA_SOURCE_BUNDLE_README_TEMPLATE', 'file', 'templates/data_tasks/bundle_readme.md', '/root/projects/trading-main/templates/data_tasks/bundle_readme.md', 'trading-data', 'draft per-bundle data source documentation template'),
  ('out_HPQNDFZT', 'output', 'DATA_SOURCE_FETCH_SPEC_TEMPLATE', 'file', 'templates/data_tasks/fetch_spec.md', '/root/projects/trading-main/templates/data_tasks/fetch_spec.md', 'trading-data', 'draft API/source fetch requirement template for historical data bundles'),
  ('out_BHT4A23J', 'output', 'DATA_SOURCE_CLEAN_SPEC_TEMPLATE', 'file', 'templates/data_tasks/clean_spec.md', '/root/projects/trading-main/templates/data_tasks/clean_spec.md', 'trading-data', 'draft clean/normalization requirement template for historical data bundles'),
  ('out_6ASNKM52', 'output', 'DATA_SOURCE_SAVE_SPEC_TEMPLATE', 'file', 'templates/data_tasks/save_spec.md', '/root/projects/trading-main/templates/data_tasks/save_spec.md', 'trading-data;trading-storage', 'draft development-save and future durable-save requirement template'),
  ('out_ERYNXVJ3', 'output', 'DATA_TASK_COMPLETION_RECEIPT_TEMPLATE', 'file', 'templates/data_tasks/completion_receipt.json', '/root/projects/trading-main/templates/data_tasks/completion_receipt.json', 'trading-data;trading-manager;trading-storage', 'draft completion receipt template for development receipts and later durable receipt contracts'),
  ('out_HGBSWHKM', 'output', 'DATA_SOURCE_FIXTURE_POLICY_TEMPLATE', 'file', 'templates/data_tasks/fixture_policy.md', '/root/projects/trading-main/templates/data_tasks/fixture_policy.md', 'trading-data', 'draft fixture and live-call guardrail template for data source bundles')
ON CONFLICT (id) DO UPDATE
SET
  kind = EXCLUDED.kind,
  key = EXCLUDED.key,
  payload_format = EXCLUDED.payload_format,
  payload = EXCLUDED.payload,
  path = EXCLUDED.path,
  applies_to = EXCLUDED.applies_to,
  note = EXCLUDED.note;
