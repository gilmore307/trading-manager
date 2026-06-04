# Monthly Backfill

Monthly backfill planning creates deterministic manager requests for historical provider data and feature preparation.

## Purpose

- Split historical work into reviewable month windows.
- Keep provider calls behind explicit dispatch gates.
- Produce request payloads and input bindings that components can execute.
- Reuse valid point-in-time data/features/coverage evidence.

## Normal Flow

```text
plan monthly window
-> create manager_request rows or dry-run previews
-> materialize request payloads
-> validate handoff
-> dispatch provider acquisition only with explicit provider flag
-> reconcile completion receipts
-> record artifacts/ready signals
```

## Layer 1/2 Foundation Catch-up

Layer 1 market/cross-asset and Layer 2 broad sector-anchor data are targetless foundation panels. During catch-up, these panels advance before ordinary Layer 3+ target work.

Valid provider data, cleaned monthly data, deterministic features, feature-ready manifests, and coverage evidence may be reused when their point-in-time semantics and schema still match. Dependent model/evaluation/promotion artifacts must be rebuilt when their substrate changed.

## Primary Commands

```bash
PYTHONPATH=src python3 scripts/tasks/plan_monthly_backfill.py --start-month 2016-01 --end-month 2016-03 --format jsonl
PYTHONPATH=src python3 scripts/tasks/prepare_layer_one_historical_training.py --start-month 2016-01 --end-month 2016-01 --write-files-only --format json
PYTHONPATH=src python3 scripts/tasks/prepare_layer_two_historical_training.py --start-month 2016-01 --end-month 2016-01 --write-files-only --format json
PYTHONPATH=src python3 scripts/tasks/dispatch_provider_acquisition.py --start-month 2016-01 --end-month 2016-01 --model-layer layer_01_market_regime --execute-provider-calls
```

Without the explicit provider-dispatch flag, planning and handoff validation must not call providers.
