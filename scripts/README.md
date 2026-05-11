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
- `tasks/plan_model_training_workflow.py` — emits the manager-owned Layer 1-8 historical model-training workflow graph, including data acquisition, feature, generation, evaluation, review, and maintenance stages.
- `tasks/collect_dataset_evidence.py` — collects current snapshot/split/label/eval/control-plane evidence into `manager_dataset_evidence_v1` for expansion planning without provider calls.
- `tasks/plan_dataset_expansion.py` — lets manager choose the next dataset role/layer to expand, and with `--write` prepares the selected safe artifacts/payloads without provider calls.
- `tasks/advance_model_training_workflow.py` — refreshes the durable Layer 1-8 workflow checkpoint, ingests component receipts, records reviewed approval refs, and selects the next safe/gated stage.
- `tasks/plan_live_call_approval.py` — creates a skip-aware live-call approval review proposal/template without approving, dispatching, or calling providers; `--pending-only` excludes ready/reviewed-terminal stage requests.
- `tasks/create_live_call_approval_packet.py` — writes a complete local approval packet bundle with proposal, reviewed-approval placeholder, validation/dispatch/reconcile command templates, status command, and zero provider calls; use `--pending-only` for normal runtime packets.
- `tasks/inspect_live_call_approval_packet.py` — inspects packet lifecycle status (`template_pending_review` through `reconciled`) without approving, dispatching, or calling providers.
- `tasks/rehearse_live_call_approval_packet.py` — rehearses proposal validation plus plan-only dispatch through ephemeral approval files, leaving persistent packet state unchanged and provider calls at zero.
- `tasks/validate_live_call_approval_proposal.py` — validates a reviewed `live_call_approval_v1` exactly against a manager proposal before any dispatch attempt.
- `tasks/dispatch_approved_provider_acquisition.py` — validates `live_call_approval_v1` for Layer 1/2 Alpaca-bars provider acquisition selected by `--model-layer` and, only with both `--execute-approved-provider-calls` and exact `--approval-validation`, runs the approved trading-data commands.
- `tasks/reconcile_provider_stage.py` — safely reconciles existing provider-stage completion receipts into manager control-plane rows, stage coverage, and workflow state without dispatching providers.
- `tasks/validate_live_call_approval.py` — validates reviewed `live_call_approval_v1` artifacts before any non-dry-run provider handoff is considered.
- `tasks/execute_model_training_stage.py` — executes one ready safe offline workflow stage, writes stdout/stderr logs and a component receipt, and refuses provider-gated stages.
- `tasks/prepare_layer_one_historical_training.py` — manager-owned Layer 1 batch preparation: plans the full market-regime ETF universe, materializes payloads, and validates handoff boundaries without provider dispatch.
- `tasks/prepare_layer_two_historical_training.py` — manager-owned Layer 2 batch preparation: plans the full sector/industry ETF universe, materializes payloads, and validates handoff boundaries without provider dispatch.
- `tasks/run_automation_scheduler.py` — runs one capacity-aware scheduler tick: applies regular-trading-day market-hours protection, resource gates, and either reports or executes safe offline Layer 1 preparation without provider dispatch.
- `tasks/run_automation_scheduler_daemon.py` — runs the persistent checkpointed historical-training scheduler daemon for resident background operation under a service manager.
- `tasks/submit_manager_requests.py` — validates or persists manager request rows.
- `tasks/materialize_request_payloads.py` — writes component-readable parameter payloads behind `parameter_ref` and can persist request-scoped `input_binding_v1` metadata.
- `tasks/validate_request_handoff.py` — validates materialized request payloads against component `build_context` paths without dispatching work or calling providers.
- `tasks/record_completion_receipt.py` — normalizes or persists component completion receipts into manager run/artifact/ready rows.
- `tasks/list_task_summary.py` — lists global task summary rows in priority order.
- `tasks/rehearse_task_system.py` — runs a deterministic request/receipt/summary rehearsal without provider calls; add `--write` only to persist rehearsal-only rows to manager SQL.
- `tasks/plan_model_promotion_review.py` — plans one unified manager-side promotion-review request shape for any model layer.
- `tasks/build_review_decision.py` — builds generic `review_decision_v1` artifacts without activation side effects.

## Run

```bash
python3 scripts/registry/apply_registry_migrations.py
python3 scripts/registry/apply_registry_migrations.py --dry-run
python3 scripts/registry/apply_registry_migrations.py --export-only
PYTHONPATH=src python3 scripts/tasks/plan_monthly_backfill.py --start-month 2016-01 --end-month 2016-03 --format jsonl
PYTHONPATH=src python3 scripts/tasks/plan_model_training_workflow.py --start-month 2016-01 --end-month 2016-01
PYTHONPATH=src python3 scripts/tasks/advance_model_training_workflow.py --start-month 2016-01 --end-month 2016-01 --write
PYTHONPATH=src python3 scripts/tasks/collect_dataset_evidence.py --write --output-path storage/runtime/dataset_expansion/evidence.json
PYTHONPATH=src python3 scripts/tasks/plan_dataset_expansion.py --start-month 2016-01 --end-month 2016-01
PYTHONPATH=src python3 scripts/tasks/plan_dataset_expansion.py --collect-evidence-from-db --start-month 2016-01 --end-month 2016-01
PYTHONPATH=src python3 scripts/tasks/dispatch_approved_provider_acquisition.py --start-month 2016-01 --end-month 2016-01 --approval storage/runtime/live_call_approval_layer_01.json
PYTHONPATH=src python3 scripts/tasks/validate_live_call_approval.py live_requests.jsonl --approval live_call_approval.json
PYTHONPATH=src python3 scripts/tasks/execute_model_training_stage.py --start-month 2016-01 --end-month 2016-01 --write
PYTHONPATH=src python3 scripts/tasks/prepare_layer_one_historical_training.py --start-month 2016-01 --end-month 2016-01 --write-files-only --format json
PYTHONPATH=src python3 scripts/tasks/prepare_layer_two_historical_training.py --start-month 2016-01 --end-month 2016-01 --write-files-only --format json
PYTHONPATH=src python3 scripts/tasks/run_automation_scheduler.py --start-month 2016-01 --end-month 2016-01
PYTHONPATH=src python3 scripts/tasks/run_automation_scheduler.py --start-month 2016-01 --end-month 2016-01 --execute-safe-preparation
PYTHONPATH=src python3 scripts/tasks/run_automation_scheduler_daemon.py --start-month 2016-01 --end-month 2016-01 --execute-safe-preparation --once
PYTHONPATH=src python3 scripts/tasks/submit_manager_requests.py requests.jsonl
PYTHONPATH=src python3 scripts/tasks/materialize_request_payloads.py requests.jsonl --write-files
PYTHONPATH=src python3 scripts/tasks/validate_request_handoff.py --from-db --request-id mgrreq_backfill_alpaca_bars_2016_01
PYTHONPATH=src python3 scripts/tasks/record_completion_receipt.py completion_receipt.json --request-id mgrreq_example --component-id component --repo-id trading-data --receipt-uri storage://example/completion_receipt.json
PYTHONPATH=src python3 scripts/tasks/list_task_summary.py --limit 50
PYTHONPATH=src python3 scripts/tasks/rehearse_task_system.py --end-month 2016-01 --limit 3 --scenario mixed --format jsonl
PYTHONPATH=src python3 scripts/tasks/plan_model_promotion_review.py --model model_08_option_expression --candidate-ref trading-model://promotion-candidates/mpcand_example
PYTHONPATH=src python3 scripts/tasks/build_review_decision.py --review-target-ref storage://trading-model/promotion-candidates/mpcand_example.json --decision-status defer --decision-reason "missing production calibration evidence"
```

The SQL `trading_registry.kind` constraint and `scripts/registry/kinds/*.md` files must stay aligned. Tests compare those sources directly.

Registry `id` is the stable automation reference. Registry `key` is a human-readable output/display label and may be renamed by reviewed migration. Helper APIs must not take key as input.
