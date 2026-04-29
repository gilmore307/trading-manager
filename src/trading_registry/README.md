# trading_registry

Python registry helper package for `trading-main`.

## Public Surface

- `RegistryReader.get_key_by_id(id)`
- `RegistryReader.get_payload_by_id(id)`
- `RegistryReader.get_path_by_id(id)`
- `SecretResolver.load_secret_text_by_config_id(config_id, field_name=None)`

Registry lookup helpers use stable registry ids as inputs. Registry keys are output/display labels only.

## Source Secret JSON

Secret configs should point to one source-level JSON file per provider/source. The config row payload is the source alias, and the optional `path` column mirrors the resolved JSON file path.

`SecretResolver.load_secret_text_by_config_id(config_id)` returns the raw JSON text.

`SecretResolver.load_secret_text_by_config_id(config_id, field_name)` returns one string field from that JSON object, such as `api_key`, `secret_key`, `passphrase`, or `pat`.


## CSV-backed registry query

`create_csv_registry_query("scripts/registry/current.csv")` provides the small query surface used by `RegistryReader` and `SecretResolver` when helper scripts need id-based registry lookups before a database connection exists.
