# Helper Tests

`helpers/tests/` owns first-party tests for the `trading-main` helper package.

## Boundary

- Test scripts are repository-local verification assets, not registry entries.
- Do not register test files as registry `script` rows.
- Every first-party `test_*.py` script in this directory must be listed in the inventory below with what it verifies.
- Update this README whenever a test script is added, renamed, split, merged, or removed.

## Inventory

- `test_trading_registry.py` verifies:
  - id-based `RegistryReader` lookup, required lookup, path, payload, key, and kind-filter behavior;
  - registry row mapping into `RegistryItem` objects;
  - secret alias parsing and id-based secret resolution behavior;
  - SQL `kind` constraint alignment with `registry/kinds/*.md` and active `registry/current.csv` rows;
  - SQL `payload_format` constraint alignment with registered `kind=payload_format` rows;
  - test-script governance: first-party test scripts are documented here and are not registered as registry `script` rows.

## Run

From the repository root:

```bash
/root/projects/trading-main/.venv/bin/python -m unittest discover -s helpers/tests
```
