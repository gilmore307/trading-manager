-- Point registry helper script rows at the formal Python runtime helper surface.
-- Target engine: PostgreSQL.

UPDATE trading_registry
SET
  payload = 'RegistryReader.get_key_by_id',
  path = '/root/projects/trading-main/helpers/python/trading_registry/reader.py',
  applies_to = 'helpers/python/trading_registry',
  note = 'official Python runtime helper that returns a registry item key or null by stable id'
WHERE id = 'scr_GK1D8P4Q';

UPDATE trading_registry
SET
  payload = 'RegistryReader.get_payload_by_id',
  path = '/root/projects/trading-main/helpers/python/trading_registry/reader.py',
  applies_to = 'helpers/python/trading_registry',
  note = 'official Python runtime helper that returns a registry item payload or null by stable id'
WHERE id = 'scr_GP2L7M9A';

UPDATE trading_registry
SET
  payload = 'RegistryReader.get_path_by_id',
  path = '/root/projects/trading-main/helpers/python/trading_registry/reader.py',
  applies_to = 'helpers/python/trading_registry',
  note = 'official Python runtime helper that returns a registry item path or null by stable id'
WHERE id = 'scr_GH6V3T8N';

UPDATE trading_registry
SET
  payload = 'SecretResolver.load_secret_text_by_config_id',
  path = '/root/projects/trading-main/helpers/python/trading_registry/secret_resolver.py',
  applies_to = 'helpers/python/trading_registry',
  note = 'official Python runtime helper that resolves a config payload secret alias and returns trimmed secret text by stable config id'
WHERE id = 'scr_LS5Q2K7W';
