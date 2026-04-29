-- Register the default data source bundle pipeline implementation template.
-- Target engine: PostgreSQL.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, note)
VALUES
  ('out_LHUMWZSL', 'output', 'DATA_SOURCE_PIPELINE_TEMPLATE', 'file', 'templates/data_tasks/pipeline.py', '/root/projects/trading-main/templates/data_tasks/pipeline.py', 'trading-data', 'default single-file bundle implementation template with run plus fetch/clean/save/write_receipt step functions; split into modules only when complexity justifies it')
ON CONFLICT (id) DO UPDATE
SET
  kind = EXCLUDED.kind,
  key = EXCLUDED.key,
  payload_format = EXCLUDED.payload_format,
  payload = EXCLUDED.payload,
  path = EXCLUDED.path,
  applies_to = EXCLUDED.applies_to,
  note = EXCLUDED.note;
