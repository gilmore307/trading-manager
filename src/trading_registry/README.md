# trading_registry

`trading_registry` is the Python helper package for id-based registry lookup and secret-alias resolution.

## Public Surface

```text
RegistryReader.get_key_by_id(id)
RegistryReader.get_payload_by_id(id)
RegistryReader.get_path_by_id(id)
SecretResolver.load_secret_text_by_config_id(config_id, field_name=None)
create_csv_registry_query(path)
```

## Rules

- Helper inputs use stable registry ids, not mutable registry keys.
- Keys are display/search labels.
- Secret configs resolve aliases; they must not expose or store secret values in Git.
- Source-level secrets should normally be one JSON file per provider/source.

## CSV Query Mode

`create_csv_registry_query("scripts/registry/current.csv")` provides the small lookup surface used before a database connection exists.
