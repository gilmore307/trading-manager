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

`helpers/` is not currently a formal cross-repository runtime package. There is no package metadata, version policy, runtime engine declaration, installation command, or import contract.

Current JavaScript helpers under `helpers/registry/` are internal `trading-main` maintenance/test helpers until a Node package, Python package, or internal-only strategy is explicitly accepted in `docs/07_helpers.md` and `docs/05_decision.md`.
