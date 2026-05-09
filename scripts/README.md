# Scripts

`scripts/` stores executable maintenance and operational entrypoints for `trading-manager`.

Registry maintenance is grouped under `scripts/registry/`. Task-planning commands live under `scripts/tasks/` so control-plane planning does not mix with registry migration mechanics.

For the docs-level registry guide, see [`docs/91_registry.md`](../docs/91_registry.md).

## Boundary

- Scripts may import reusable implementation from `src/`.
- `src/` must not import `scripts/`.
- Scripts are callable entrypoints, not ordinary package source files.
- Stable cross-repository or automation-facing commands should be registered as `kind=script` rows in the registry.
- Registry SQL, generated CSV snapshots, kind boundaries, and registry rules live under `scripts/registry/`.

## Inventory

- `registry/apply_registry_migrations.py` — applies pending SQL registry migrations exactly once and exports `scripts/registry/current.csv` unless `--no-export` is used.
- `registry/current.csv` — generated GitHub-visible snapshot of the active `trading_registry` table; do not hand-edit it.
- `registry/kinds/` — one Markdown boundary file per registry kind. These files define scope/range/rejection boundaries only, not concrete active row lists.
- `registry/rules/` — normative registry table, kind-routing, and naming rules that constrain SQL row shape.
- `registry/sql/schema_migrations/` — append-only SQL migrations for registry schema and active row changes.
- `tasks/plan_monthly_backfill.py` — emits deterministic dry-run `manager_request_v1` rows for monthly historical data backfill planning.
- `tasks/submit_manager_requests.py` — validates or persists manager request rows.
- `tasks/record_completion_receipt.py` — normalizes or persists component completion receipts into manager run/artifact/ready rows.
- `tasks/list_task_summary.py` — lists global task summary rows in priority order.
- `tasks/rehearse_task_system.py` — runs a deterministic in-memory request/receipt/summary rehearsal without provider calls or SQL writes.
- `tasks/plan_model_promotion_review.py` — plans one unified manager-side promotion-review request shape for any model layer.

## Run

```bash
python3 scripts/registry/apply_registry_migrations.py
python3 scripts/registry/apply_registry_migrations.py --dry-run
python3 scripts/registry/apply_registry_migrations.py --export-only
PYTHONPATH=src python3 scripts/tasks/plan_monthly_backfill.py --start-month 2016-01 --end-month 2016-03 --format jsonl
PYTHONPATH=src python3 scripts/tasks/submit_manager_requests.py requests.jsonl
PYTHONPATH=src python3 scripts/tasks/record_completion_receipt.py completion_receipt.json --request-id mgrreq_example --component-id component --repo-id trading-data --receipt-uri storage://example/completion_receipt.json
PYTHONPATH=src python3 scripts/tasks/list_task_summary.py --limit 50
PYTHONPATH=src python3 scripts/tasks/rehearse_task_system.py --end-month 2016-01 --limit 3 --scenario mixed --format jsonl
PYTHONPATH=src python3 scripts/tasks/plan_model_promotion_review.py --model model_08_option_expression --candidate-ref trading-model://promotion-candidates/mpcand_example
```

The SQL `trading_registry.kind` constraint and `scripts/registry/kinds/*.md` files must stay aligned. Tests compare those sources directly.

Registry `id` is the stable automation reference. Registry `key` is a human-readable output/display label and may be renamed by reviewed migration. Helper APIs must not take key as input.
