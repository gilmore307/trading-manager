# Dataset Expansion Policy

Status: accepted manager-control policy for historical model training; no provider-call, promotion, or broker approval implied

## Purpose

`trading-manager` owns the decision about which historical-training dataset role needs expansion next. Operators should not have to manually choose whether the next batch expands train, calibration, validation, test, forward holdout, or shadow-monitoring evidence.

The manager decision is still bounded by hard gates:

- historical provider calls require reviewed `live_call_approval_v1`;
- model activation requires an approving `review_decision_v1`;
- broker/order/fill/account mutation remains execution-owned and forbidden here.

## Dataset roles

Manager treats dataset roles as an ordered evidence ladder:

| Role | Purpose | Selection rule |
|---|---|---|
| `train` | Fit model parameters. | Fill first for the earliest layer with missing minimum coverage. |
| `calibration` | Calibrate thresholds, ranks, probabilities, and score scales. | Fill after train and before validation/test. |
| `validation` | Tune model choices and compare candidates. | Fill after calibration. |
| `test` | Frozen promotion holdout for final review evidence. | Fill after validation; do not use for tuning. |
| `forward_holdout` | Out-of-time evidence for drift, regime coverage, and split stability. | Fill when promotion gaps require more out-of-time evidence after minimum train/calibration/validation/test coverage exists. |
| `shadow_monitoring` | Post-approval observation evidence without broker mutation. | Only selected after a layer is production-approved. |

Default planning minimums are intentionally conservative placeholders until measured production evidence supersedes them:

```text
train=60 months
calibration=12 months
validation=12 months
test=12 months
forward_holdout=6 months
shadow_monitoring=1 month
```

These defaults are manager planning thresholds, not promotion approval by themselves.

## Decision discipline

The manager walks layers in dependency order and expands the earliest layer with a blocking evidence gap.

1. Do not expand downstream layer datasets before required upstream train/calibration/validation/test coverage exists.
2. Fill train, then calibration, then validation, then test.
3. Use `forward_holdout` only after the base split ladder exists and evidence gaps such as coverage, drift, split stability, stale holdout, regime coverage, or baseline instability remain.
4. Use `shadow_monitoring` only for production-approved layers, and never as a substitute for offline promotion evidence.
5. Every expansion plan must preserve point-in-time/no-future/no-downstream-leakage discipline.
6. Dataset snapshots and splits remain frozen evidence; if expansion changes the sample universe, it creates a new snapshot/split lineage rather than silently rewriting reviewed evidence.

## Evidence collection

The expansion planner consumes manager-visible evidence; it must not invent missing-dataset status from a second decision-rule system.

The evidence collector emits `manager_dataset_evidence_v1` by inventorying existing durable evidence where available:

- `trading_model.model_dataset_snapshot`;
- `trading_model.model_dataset_split`;
- `trading_model.model_eval_label`;
- `trading_model.model_eval_run`;
- `trading_model.model_promotion_metric`;
- manager `artifact_ref_v1` / `ready_signal_v1` records.

The collector summarizes per-layer/per-role coverage with month counts, sample counts, snapshot/split refs, label/eval coverage, artifact/ready-signal counts, and promotion gaps. It performs no provider calls, no model activation, and no broker/order/fill/account mutation.

## Implementation surface

The manager evidence entrypoint is:

```bash
PYTHONPATH=src python3 scripts/tasks/collect_dataset_evidence.py \
  --write \
  --output-path storage/runtime/dataset_expansion/evidence.json
```

The manager planner entrypoint is:

```bash
PYTHONPATH=src python3 scripts/tasks/plan_dataset_expansion.py \
  --start-month 2016-01 \
  --end-month 2016-01
```

Optional evidence can be supplied as JSON:

```bash
PYTHONPATH=src python3 scripts/tasks/plan_dataset_expansion.py \
  --evidence storage/runtime/dataset_expansion/evidence.json
```

Or collected directly from SQL immediately before planning:

```bash
PYTHONPATH=src python3 scripts/tasks/plan_dataset_expansion.py \
  --collect-evidence-from-db \
  --start-month 2016-01 \
  --end-month 2016-01
```

Add `--write` only to let manager prepare the selected safe expansion artifacts/payloads. For Layer 1, this writes the full Alpaca ETF task-key payload set and handoff validation evidence, but still performs zero provider calls. Actual provider dispatch remains blocked until `live_call_approval_v1` is validated and `dispatch_approved_provider_acquisition.py --execute-approved-provider-calls` is explicitly used.

The emitted contracts are `manager_dataset_evidence_v1` and `manager_dataset_expansion_plan_v1`.

## Non-goals

This policy does not authorize:

- unattended provider dispatch;
- changing test/holdout boundaries after seeing bad results;
- model promotion or activation;
- live broker/order/fill/account mutation;
- treating shadow observations as current-version training rows without a new reviewed dataset snapshot.
