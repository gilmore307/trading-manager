# Dataset Expansion

Dataset expansion decides which historical dataset role should be broadened next.

## Purpose

- Inspect current snapshot/split/label/eval/control-plane coverage.
- Select the next safe layer or dataset role to expand.
- Prepare safe artifacts/payloads without provider calls unless explicitly dispatched.
- Keep historical sampling separate from realtime inference routing.

## Expansion Order

1. M01/M02 foundation coverage plus fold-scoped global/sector M03 event-impact substrate.
2. M02 target-state target windows.
3. Layers 4-9 downstream risk-policy/context/action/guidance chains once prerequisites exist.
4. Concentrated replay.
5. Replay review over the post-replay component funnel.
6. M06 post-replay event-risk attribution with reviewed event families and strict non-overlap rules.

## Dataset Unit

For M02+ target work, the ordinary substrate unit is one target symbol over the same 18-month `12+3+3` walk-forward fold used by model training. M01/M02 foundation work is targetless panel work. Global/sector M03 event-impact substrate is targetless but fold-scoped because the accepted observation pool can change by fold.

## Commands

```bash
PYTHONPATH=src python3 scripts/tasks/collect_dataset_evidence.py --write --output-path /root/projects/trading-storage/storage/02_control_plane/runtime/dataset_expansion/evidence.json
PYTHONPATH=src python3 scripts/tasks/plan_dataset_expansion.py --start-month 2016-01 --end-month 2016-01
PYTHONPATH=src python3 scripts/tasks/plan_dataset_expansion.py --collect-evidence-from-db --start-month 2016-01 --end-month 2016-01
```

## Realtime Rule

Historical expansion evidence can support later realtime validation, but it does not itself authorize realtime trading, shadow execution, broker calls, or production activation.
