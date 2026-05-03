-- Align registry paths with src/scripts repository architecture.
-- Target engine: PostgreSQL.

UPDATE trading_registry
SET payload = 'scripts/apply_registry_migrations.py --export-only',
    path = '/root/projects/trading-main/scripts/apply_registry_migrations.py',
    note = 'maintenance helper command that exports the active trading_registry table to registry/current.csv'
WHERE kind = 'script'
  AND key = 'REGISTRY_EXPORT_CURRENT_CSV_HELPER';

UPDATE trading_registry
SET path = '/root/projects/trading-main/src/trading_registry/reader.py',
    applies_to = 'src/trading_registry'
WHERE kind = 'script'
  AND key IN (
    'REGISTRY_GET_KEY_BY_ID_HELPER',
    'REGISTRY_GET_PATH_BY_ID_HELPER',
    'REGISTRY_GET_PAYLOAD_BY_ID_HELPER'
  );

UPDATE trading_registry
SET path = '/root/projects/trading-main/src/trading_registry/secret_resolver.py',
    applies_to = 'src/trading_registry;source_secret_json'
WHERE kind = 'script'
  AND key = 'REGISTRY_LOAD_SECRET_TEXT_BY_CONFIG_ID_HELPER';
