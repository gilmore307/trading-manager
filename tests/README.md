# Tests

`tests/` owns first-party tests for the `trading-main` source packages and repository governance checks.

## Boundary

- Test scripts are repository-local verification assets, not registry entries.
- Do not register test files as registry `script` rows.
- Every first-party `test_*.py` script in this directory must be listed in the inventory below with what it verifies.
- Update this README whenever a test script is added, renamed, split, merged, or removed.

## Inventory

- `test_trading_bigquery.py` verifies:
  - BigQuery query-result metadata parsing for dry-run byte estimates;
  - query request payload handling for `maximumBytesBilled` and dry-run flags.

- `test_trading_registry.py` verifies:
  - id-based `RegistryReader` lookup, required lookup, path, payload, key, and kind-filter behavior;
  - registry row mapping into `RegistryItem` objects;
  - source-level secret JSON alias parsing and id-based secret field resolution behavior;
  - SQL `kind` constraint alignment with `registry/kinds/*.md` and active `registry/current.csv` rows;
  - SQL `payload_format` constraint alignment with registered `kind=payload_format` rows;
  - SQL `artifact_sync_policy` constraint alignment with registered `kind=artifact_sync_policy` rows;
  - test-script governance: first-party test scripts are documented here and are not registered as registry `script` rows.

## Run

From the repository root:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
```
