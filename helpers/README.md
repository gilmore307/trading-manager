# Helpers

`helpers/` stores shared helper code used across trading repositories.

Allowed here:

- generic SQL helpers;
- artifact path/reference helpers;
- manifest helpers;
- request and ready-signal helpers;
- shared validation utilities.

Not allowed here:

- component runtime implementations;
- broker/exchange trading daemons;
- strategy logic;
- model training logic;
- dashboard application code;
- secrets or credentials.

Helper interfaces should stay explicit and reusable. Once helper behavior exists, acceptance should include tests.

See `../docs/07_helpers.md` for the docs-level helper operating guide.

## Package Status

The formal cross-repository helper runtime surface is Python. Package metadata lives in root `pyproject.toml` and source lives under `helpers/python/`.

Install from the shared environment:

```bash
/root/projects/trading-main/.venv/bin/python -m pip install -r /root/projects/trading-main/requirements.txt
/root/projects/trading-main/.venv/bin/python -m pip install -e /root/projects/trading-main
```
