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

## Historical sampling vs live routing

Dataset expansion must distinguish two universes:

| Universe | Meaning | Manager behavior |
|---|---|---|
| Historical training sampling universe | Rows collected to fit, calibrate, validate, and test a layer. | May be broader than live routing when broader sampling improves regime, sector, event, liquidity, or edge-case coverage. |
| Live inference routing universe | Rows that reach a layer in actual decision flow after upstream gates and prioritization. | May be narrower and must preserve the accepted live model handoff boundaries. |

The manager must not assume that historical expansion for a downstream layer is limited to the rows that upstream layers would route in live operation. Upstream model outputs can be attached as point-in-time context without being used as hard historical-training filters.

Layer 3 is the main rule: live routing may send targets from Layer 2 selected/prioritized sector baskets, but historical dataset expansion may sample anonymous targets across other sectors, industries, styles, market caps, liquidity tiers, and ETF/stock exposure paths. This allows the model to learn sector-confirmed, sector-divergent, strong-in-weak-sector, and weak-in-strong-sector target behavior.

When the historical sampling universe is broader than live routing, manager evidence should preserve both views:

- broad historical generalization evidence;
- live-route simulation evidence using the accepted upstream routing policy;
- subpopulation/stress slices by sector, liquidity tier, regime, event type, and routed-vs-unrouted membership where available.

## Decision discipline

The manager walks layers in dependency order and expands the earliest layer with a blocking evidence gap, but the unit of expansion differs by layer segment.

1. Layers 1-2 are finite panel flows: continue chronological months after each layer's own month-level receipts are ready; do not wait for downstream Layers 3-8.
2. Layers 3-7 are target-major serial flows: select one target candidate, complete Layers 3 -> 4 -> 5 -> 6 -> 7 for that target, then admit the next target candidate unless a reviewed coverage exception is recorded.
3. Layer 8 is option-expression expansion and begins only after the selected target's upstream Layer 1-7 context/target chain is complete.
4. Fill train, then calibration, then validation, then test.
5. Use `forward_holdout` only after the base split ladder exists and evidence gaps such as coverage, drift, split stability, stale holdout, regime coverage, or baseline instability remain.
6. Use `shadow_monitoring` only for production-approved layers, and never as a substitute for offline promotion evidence.
7. Every expansion plan must preserve point-in-time/no-future/no-downstream-leakage discipline.
8. Dataset snapshots and splits remain frozen evidence; if expansion changes the sample universe, it creates a new snapshot/split lineage rather than silently rewriting reviewed evidence.

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
