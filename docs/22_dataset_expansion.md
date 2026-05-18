# Dataset Expansion

Dataset expansion decides which historical dataset role should be broadened next.

## Purpose

- Inspect current snapshot/split/label/eval/control-plane coverage.
- Select the next safe layer or dataset role to expand.
- Prepare safe artifacts/payloads without provider calls unless explicitly dispatched.
- Keep historical sampling separate from realtime inference routing.

## Expansion Order

1. Layer 1/2 foundation coverage.
2. Layer 3 target-state target windows.
3. Layers 4-8 downstream context/action/guidance chains once prerequisites exist.
4. Layer 8 event-risk evidence as a residual lane with reviewed event families and strict non-overlap rules.

## Dataset Unit

For Layer 3+ target work, the ordinary unit is one target symbol over a bounded historical window. Layer 1/2 foundation work is targetless panel work.

## Commands

```bash
PYTHONPATH=src python3 scripts/tasks/collect_dataset_evidence.py --write --output-path storage/runtime/dataset_expansion/evidence.json
PYTHONPATH=src python3 scripts/tasks/plan_dataset_expansion.py --start-month 2016-01 --end-month 2016-01
PYTHONPATH=src python3 scripts/tasks/plan_dataset_expansion.py --collect-evidence-from-db --start-month 2016-01 --end-month 2016-01
```

## Realtime Rule

Historical expansion evidence can support later realtime validation, but it does not itself authorize realtime trading, shadow execution, broker calls, or production activation.
