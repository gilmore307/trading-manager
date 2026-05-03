-- Expand registry payload_format from storage-only text/file to explicit value formats.
-- Target engine: PostgreSQL.

ALTER TABLE trading_registry
DROP CONSTRAINT IF EXISTS trading_registry_payload_format_check;

ALTER TABLE trading_registry
ADD CONSTRAINT trading_registry_payload_format_check
CHECK (payload_format IN (
  'text',
  'file',
  'json',
  'integer',
  'decimal',
  'boolean',
  'iso_date',
  'iso_time',
  'iso_datetime',
  'iso_duration',
  'timezone',
  'secret_alias',
  'repo_name',
  'field_name',
  'status_value',
  'command',
  'python_symbol'
));

UPDATE trading_registry
SET payload_format = 'field_name'
WHERE kind = 'field';

UPDATE trading_registry
SET payload_format = 'status_value'
WHERE kind IN (
  'acceptance_outcome',
  'docs_status',
  'maintenance_status',
  'review_readiness',
  'task_lifecycle_state',
  'test_status'
);

UPDATE trading_registry
SET payload_format = 'repo_name'
WHERE kind = 'repo';

UPDATE trading_registry
SET payload_format = 'timezone'
WHERE id = 'cfg_J7D1K5RP';

UPDATE trading_registry
SET payload_format = 'secret_alias'
WHERE id = 'cfg_U8C2D6YA';

UPDATE trading_registry
SET payload_format = 'command'
WHERE id = 'scr_CV8R2M5J';

UPDATE trading_registry
SET payload_format = 'python_symbol'
WHERE kind = 'script'
  AND id <> 'scr_CV8R2M5J';
