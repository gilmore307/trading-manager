# trading-manager

`trading-manager` is the control-plane repository for the trading system.

It owns the parts of the system that must be shared across repositories: architecture, registry, contracts, request routing, workflow state, scheduler policy, review gates, promotion gates, shared helper packages, and operator-facing status surfaces.

It does **not** own provider adapters, feature construction, model implementation, broker execution, durable market-data storage, dashboard UI, generated artifacts, or secrets. Those remain in the component repositories.

## First Principles

1. **Separate decision authority from component work.** Manager decides what work is valid, when it may run, and what evidence is accepted. Components perform the work.
2. **Use contracts instead of assumptions.** Requests, inputs, runs, artifacts, ready signals, promotion decisions, and scheduler checkpoints must have explicit schemas or registry-backed names.
3. **Preserve point-in-time discipline.** A downstream model or review can consume only evidence that was available at its decision time.
4. **Keep historical modeling separate from trading execution.** Historical services may acquire data, build features, evaluate models, and prepare review artifacts. They must not place orders, mutate broker/account state, or activate production models without the accepted review path.
5. **Make automation resumable.** Resident services use durable runtime state, locks, receipts, and summaries so progress does not depend on chat/session memory.

## Repository Layout

```text
docs/             Current manager documentation and governance files.
src/              Importable helper packages used by manager scripts and component repos.
scripts/          Executable registry and task-control entrypoints.
deploy/           Reviewed service templates and operator deployment notes.
tests/            Unit and governance tests.
pyproject.toml    Python package metadata.
requirements.txt  Shared environment dependency ledger.
```

## Documentation Spine

```text
docs/00_scope.md                         Boundary of this repository.
docs/01_context.md                       Repository map and operating assumptions.
docs/02_layer_01_market_regime.md        Manager boundary for Layer 1.
docs/03_layer_02_sector_context.md       Manager boundary for Layer 2.
docs/04_model_stack_control_plane.md     Current Layer 1-9 control-plane map.
docs/80_task.md                          Current active tasks and gates.
docs/81_decision.md                      Current decision ledger.
docs/82_memory.md                        Durable note policy.
docs/90_helpers.md                       Shared helper package policy.
docs/91_registry.md                      Registry operating guide.
docs/92_templates.md                     Template boundary.
docs/93_contracts.md                     Manager control-plane contracts.
docs/94_monthly_backfill.md              Historical backfill planning.
docs/95_task_system.md                   Request/receipt/task-summary lifecycle.
docs/96_model_promotion.md               Promotion and activation gates.
docs/97_manager_control_plane_closeout.md Accepted control-plane scope.
docs/98_automation_scheduler.md          Scheduler policy.
docs/99_historical_scheduler_runtime.md  Resident service runtime.
docs/100_dataset_expansion.md            Dataset expansion policy.
docs/101_controlled_information_pass.md  Safe information-pass policy.
docs/103_numbering_physical_audit.md     Current numbering and physical-name contract.
```

## Registry Rule

Concrete registry entries live in the SQL-backed `trading_registry` table.

- SQL migrations under `scripts/registry/sql/schema_migrations/` are the source of truth for active rows.
- `scripts/registry/current.csv` is generated and must not be edited by hand.
- `scripts/registry/kinds/*.md` define registry-kind boundaries, not row lists.
- `scripts/registry/rules/*.md` define cross-kind rules.
- Registry `id` values are stable automation references. Registry `key` values are human-readable and may change through reviewed migrations.

## Normal Verification

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
python3 scripts/registry/apply_registry_migrations.py --dry-run
python3 -m compileall -q src scripts
git diff --check
```

## Shared Environment

The shared trading Python environment is anchored at:

```text
/root/projects/trading-manager/.venv
```

Dependencies must be recorded in `requirements.txt` before installation. Secrets remain outside the repository and are accessed only by reviewed alias/registry mechanisms.
