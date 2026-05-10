# Automation Scheduler Policy

`trading-manager` should become the always-on automation control plane for historical model training and maintenance while preserving capacity for live trading operations.

This policy is accepted as the target scheduler shape. The first implementation is `scripts/tasks/run_automation_scheduler.py`, which runs one gated scheduler tick and can execute safe offline Layer 1 preparation only. It does not enable live provider calls, model activation, broker orders, fills, position mutation, or unattended production trading.

## Responsibility

The manager scheduler owns continuous orchestration across the full offline training lifecycle. Historical provider acquisition is part of that lifecycle, not an external manual requirement:

```text
data acquisition planning
  -> approval-gated provider acquisition dispatch
  -> source normalization
  -> feature generation
  -> model training/generation
  -> evaluation and label evidence
  -> promotion-review request
  -> approved activation artifact only after review approval
```

The scheduler should not sit idle when safe work exists. If provider calls are not yet approved, or if a regular-trading-day market-hours throttle is active, it should shift to work that does not violate gates: dataset expansion planning, approval-artifact preparation, payload preparation, handoff validation, local feature/model/evaluation jobs over materialized data, receipt normalization, artifact/reference checks, stale-failure retry planning, docs/registry consistency checks, and storage lifecycle review.

Dataset expansion is manager-owned. The manager decides whether the next expansion should target train, calibration, validation, test, forward holdout, or shadow-monitoring evidence for the earliest blocked layer. Operators may provide evidence inputs, but should not have to manually choose the dataset role. See [`100_dataset_expansion.md`](100_dataset_expansion.md).

Layer progression is segmented rather than synchronized across all models. Layers 1-2 are finite background panels and may keep moving forward by month after their own receipts are ready. Layers 3-7 are a target-major chain: complete one selected target candidate through Layer 7 before opening the next target candidate by default. Layer 8 waits for the upstream target chain before expanding option-expression contract buckets. This is the default scheduler posture unless a reviewed coverage/exception artifact says otherwise.

## Priority Order

The scheduler must preserve this priority order:

1. live trading monitoring, risk checks, and execution-owned order/fill/account lifecycle;
2. provider-call safety gates, approval expiry checks, and dispatch guardrails;
3. urgent production incident or data-integrity repair;
4. historical data acquisition that has a valid `live_call_approval_v1`;
5. offline feature generation, model training, evaluation, and promotion evidence;
6. maintenance, cleanup, documentation, and registry hygiene.

Historical training is important, but it is background work relative to live monitoring and execution.

## Resource Budget

Historical work may use concurrency, but it must be capacity-aware.

Default target posture:

- reserve a live-trading headroom budget before starting historical jobs;
- size historical worker concurrency from observed host capacity, not from a fixed constant;
- reduce or pause historical workers under CPU, memory, disk I/O, database pressure, provider rate-limit pressure, or live-system alerts;
- prefer fewer larger batches when provider/API rate limits are relevant;
- keep task boundaries restartable and receipt-backed so paused work can resume without guessing.

Until measured production capacity exists, the conservative planning assumption is that live monitoring and order-routing capacity is reserved first, and historical work runs only in the remaining budget.

## Market-Hours Policy

During regular US equity market hours on actual regular US equity trading days, manager should pause or heavily throttle historical data/modeling jobs by default.

Default window:

```text
America/New_York regular-session trading-day protection:
09:20-16:10 ET only on regular US equity trading days
```

The buffer covers pre-open checks and post-close reconciliation. The protection applies only when the US equity regular session is open that day; weekends, NYSE holidays, and other non-trading days must not trigger this pause merely because the wall clock is between 09:20 and 16:10 ET. During the protected window:

- do not start new historical provider acquisition batches;
- do not start CPU-heavy feature/model/evaluation batches;
- allow lightweight bookkeeping only when it does not contend with live systems;
- allow urgent manual override only through reviewed policy, not as a hidden default.

Outside the protected window, including non-trading days, the scheduler should resume safe queued historical work automatically subject to resource budgets and approval gates.

## Approval Gates Stay Hard

Automation does not weaken gates:

- live historical provider calls still require reviewed `live_call_approval_v1` and validation;
- model activation still requires an approving `review_decision_v1` before activation artifacts are valid;
- broker/order/fill/account mutation remains execution-owned and must not be inferred from model-training progress;
- secrets remain alias/config references only.

## Work-Loop Semantics

The scheduler implementation should behave like a durable work loop:

1. inspect `task_summary`, receipts, ready signals, and artifact refs;
2. find the next safe blocked/ready work item by priority and dependency state;
3. check market-hours/resource/provider/promotion/execution gates;
4. dispatch only the allowed component request type;
5. record receipts and update manager summary surfaces;
6. continue until no safe work exists, then sleep/backoff instead of spinning.

If no safe work exists, the scheduler should report why: waiting for approval, regular-trading-day market-hours protection, resource pressure, missing upstream artifact, failed dependency, provider quota, or promotion review.

The current one-shot scheduler tick implements the first safe step: it evaluates regular-trading-day market-hours protection and host resource pressure, then either reports `prepare_layer_one_historical_training_batch` as the next safe internal work item or executes that preparation with `--execute-safe-preparation`. Execution writes task-key payloads and validates handoff shape only. The next internal stage is `approval_gated_provider_acquisition`; the approval gate is a safety control inside historical training, not an external dependency or manual task request.

The persistent runtime entrypoint is `scripts/tasks/run_automation_scheduler_daemon.py`. It wraps the tick in a resident loop with a `manager_scheduler_daemon_state_v1` checkpoint, single-instance lock, decision JSONL log, and service-manager-ready template under `deploy/systemd/`. `scripts/tasks/plan_dataset_expansion.py` provides the explicit dataset-expansion decision surface used by the scheduler policy: plan-only by default, and `--write` prepares only safe artifacts/payloads while preserving provider, promotion, and execution gates. See [`99_historical_scheduler_runtime.md`](99_historical_scheduler_runtime.md) for boot, resume, and maintenance expectations.

## Non-Goals

This policy does not authorize:

- unattended live provider dispatch without approval;
- production model activation without promotion review approval;
- broker execution or account mutation;
- hiding long-running jobs from receipts/artifacts/summary;
- running duplicate scheduler daemons over the same lock/state path;
- saturating the host just because historical backlog exists.
