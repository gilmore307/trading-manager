# trading_registry

Python registry helper package for `trading-main`.

## Public Surface

- `RegistryReader.get_key_by_id(id)`
- `RegistryReader.get_payload_by_id(id)`
- `RegistryReader.get_path_by_id(id)`
- `SecretResolver.load_secret_text_by_config_id(config_id)`
- `REGISTRY_KINDS`, `is_registry_kind`, and `assert_registry_kind`

Registry lookup helpers use stable registry ids as inputs. Registry keys are output/display labels only.
