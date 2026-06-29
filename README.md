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
docs/00_scope.md                         Repository boundary.
docs/01_context.md                       Repository map and operating assumptions.
docs/02_architecture.md                  Current M01-M06 control-plane map.
docs/03_contracts.md                     Manager control-plane contracts.
docs/04_task.md                          Current active tasks and gates.
docs/05_decision.md                      Current decision ledger.
docs/06_memory.md                        Durable note policy.
docs/10_registry.md                      Registry operating guide.
docs/11_templates.md                     Template boundary.
docs/20_task_system.md                   Request/receipt/task-summary lifecycle.
docs/21_monthly_backfill.md              Historical backfill planning.
docs/22_dataset_expansion.md             Dataset expansion policy.
docs/23_controlled_information_pass.md   Safe information-pass policy.
docs/24_model_promotion.md               Promotion and activation gates.
docs/25_automation_scheduler.md          Scheduler policy.
docs/26_historical_scheduler_runtime.md  Resident service runtime.
docs/27_control_plane_acceptance.md      Accepted control-plane scope.
docs/28_numbering_physical_contract.md   Current numbering and physical-name contract.
docs/29_train_replay_realtime_input_parity.md  Train/replay/realtime input parity contract.
docs/30_helpers.md                       Shared helper package policy.
```

## Registry Rule

Concrete registry entries live in the SQL-backed `trading_registry` table.

- `scripts/registry/sql/trading_registry.sql` is the current table definition.
- `scripts/registry/current.csv` is the reviewed current row inventory and DB sync source.
- `scripts/registry/kinds/*.md` define registry-kind boundaries, not row lists.
- `scripts/registry/rules/*.md` define cross-kind rules.
- Registry `id` values are stable automation references. Registry `key` values are human-readable and may change through reviewed registry updates.

## Normal Verification

Clean local/CI environments without database credentials use the no-DB registry snapshot check:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
python3 scripts/docs/check_docs_spine.py
python3 scripts/docs/check_layer_tokens.py
python3 scripts/contracts/validate_contract_examples.py
python3 scripts/registry/check_registry_current_matches_db.py --allow-missing-db
python3 -m compileall -q src scripts
git diff --check
```

Operator/server environments with registry DB access should additionally run the strict DB-backed registry gate:

```bash
python3 scripts/registry/sync_registry.py --dry-run
python3 scripts/registry/check_registry_current_matches_db.py
```

## Shared Environment

The shared trading Python environment is anchored at:

```text
/root/projects/trading-manager/.venv
```

Dependencies must be recorded in `requirements.txt` before installation. Secrets remain outside the repository and are accessed only by reviewed alias/registry mechanisms.
