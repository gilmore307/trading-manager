# Automation Scheduler Policy

`trading-manager` should become the always-on automation control plane for historical model training and maintenance while preserving capacity for live trading operations.

This policy is accepted as the target scheduler shape. The first implementation is `scripts/tasks/run_automation_scheduler.py`, which runs one gated scheduler tick and can execute safe offline Layer 1 preparation only. It does not enable live provider calls, model activation, broker orders, fills, position mutation, or unattended production trading.

## Responsibility

The manager scheduler owns continuous orchestration across the full offline training lifecycle. Historical provider acquisition is part of that lifecycle, not an external manual requirement:

```text
data acquisition planning
  -> autonomous historical provider acquisition dispatch
  -> source normalization
  -> feature generation
  -> model training/generation
  -> evaluation and label evidence
  -> promotion-review request
  -> agent decision artifact for production promotion/activation
```

The scheduler should not sit idle when safe work exists. If provider calls are waiting on bounded controls/validation, or if a regular-trading-day market-hours throttle is active, it should shift to work that does not violate gates: dataset expansion planning, decision-artifact preparation, payload preparation, handoff validation, local feature/model/evaluation jobs over materialized data, receipt normalization, artifact/reference checks, stale-failure retry planning, docs/registry consistency checks, and storage lifecycle rule evaluation.

Dataset expansion is manager-owned. The manager decides whether the next expansion should target train, calibration, validation, test, forward holdout, or shadow-monitoring evidence for the earliest blocked layer. Operators may provide evidence inputs, but should not have to manually choose the dataset role. See [`100_dataset_expansion.md`](100_dataset_expansion.md). Before widening unresolved defaults, run the 2016-01 controlled information pass in [`101_controlled_information_pass.md`](101_controlled_information_pass.md).

Layer progression is segmented rather than synchronized across all models. Layers 1-2 are finite background panels and may keep moving forward by month after their own receipts are ready. Layers 3-7 are a target-major chain: complete one selected target candidate through Layer 7 before opening the next target candidate by default. Layer 8 waits for the upstream target chain before expanding option-expression contract buckets. This is the default scheduler posture unless a reviewed coverage/exception artifact says otherwise.

Layer 8 option buckets expand from near expirations to farther expirations: current listed week first, then next listed week, then the following listed week, continuing outward only when coverage policy requires it. For each selected target, the strike bucket is the listed-strike corridor from current underlying reference price to Layer 7 target price plus three listed strike levels below the corridor and three listed strike levels above it. Example: current `95`, target `100`, one-dollar listed strikes -> `92` through `103`. Historical model-construction buckets intentionally do not prefilter out illiquid, wide-spread, low-OI, high-IV, deep ITM/OTM, or otherwise extreme contracts; those observations are needed for robustness and should become features/labels/reason codes rather than acquisition-time exclusions. V1 expression coverage is single-leg only: long call, long put, or no-option expression.

## Priority Order

The scheduler must preserve this priority order:

1. live trading monitoring, risk checks, and execution-owned order/fill/account lifecycle;
2. provider-call safety gates, agent-review expiry checks, and dispatch guardrails;
3. urgent production incident or data-integrity repair;
4. historical data acquisition through autonomous bounded provider dispatch and reconciliation;
5. offline feature generation, model training, evaluation, and promotion evidence;
6. maintenance, cleanup, documentation, and registry hygiene.

Historical training is important, but it is background work relative to live monitoring and execution.

Realtime monitoring itself is not manager-controlled. The historical scheduler may reserve capacity for realtime monitoring/execution and back off under protection policy, but live observe process lifecycle, provider stream lifecycle, subscriptions, throttling, reconnect/backoff, and runtime health belong to `trading-execution`. Manager consumes append-only receipts/evidence; it does not operate the monitor loop.

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

During regular US equity market hours on actual regular US equity trading days, manager should pause or heavily throttle historical data/modeling jobs once there is a production model/live-monitoring capacity target to protect. During the current pre-promotion phase, no model is active yet, so the resident historical scheduler runs in full-training mode with market-hours historical-training protection disabled while provider, promotion, resource, and broker gates remain hard.

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

Outside the protected window, including non-trading days, the scheduler should resume safe queued historical work automatically subject to resource budgets, agent model-promotion decisions, and storage lifecycle policy gates. Before production model activation or live trading is enabled, set `TRADING_MANAGER_MARKET_HOURS_PROTECTION_ENABLED=true` in the service environment to restore market-hours protection.

## Agent Decision Gates Stay Hard

Automation does not weaken gates:

- historical provider/data acquisition is autonomous once manager request payloads are prepared and resource gates pass;
- model activation is decided by the agent through script-called `agent_model_promotion_decision`; only an agent-approved decision can produce a valid activation artifact;
- broker/order/fill/account mutation remains execution-owned and must not be inferred from model-training progress;
- secrets remain alias/config references only.

## Work-Loop Semantics

The scheduler implementation should behave like a durable work loop:

1. inspect `task_summary`, receipts, ready signals, and artifact refs;
2. find the next safe blocked/ready work item by priority and dependency state;
3. check market-hours/resource/provider/promotion/storage/execution gates;
4. dispatch only the allowed component request type after its specific guardrails pass;
5. record receipts and update manager summary surfaces;
6. continue until no safe work exists, then sleep/backoff instead of spinning.

If no safe work exists, the scheduler should report why: waiting for agent decision, regular-trading-day market-hours protection, resource pressure, missing upstream artifact, failed dependency, provider quota, or promotion review. The scheduler should distinguish failed dependencies from valid absent history: not-yet-listed symbols and reviewed provider no-data responses are terminal evidence for the acquisition request and should flow into coverage/missingness diagnostics instead of being retried indefinitely or treated as successful positive-row data. If a component receipt is technically failed, downstream progression may use an accepted-failure coverage exception only after an agent evaluates every failed request and records the analysis artifact; the original failed task state remains visible.

The current scheduler tick evaluates regular-trading-day market-hours protection and host resource pressure, then admits one safe unit of historical work: preparation, a ready safe/offline workflow stage, a bounded gate/backoff decision, or terminal month completion. Safe/offline execution writes deterministic local artifacts, logs, receipts, and workflow state only; provider dispatch runs autonomously under manager request/resource/coverage controls, while model activation, storage lifecycle mutation, and broker/account mutation stay behind their separate boundaries.

The persistent runtime entrypoint is `scripts/tasks/run_automation_scheduler_daemon.py`. It wraps the tick in a resident system-service loop with a `manager_scheduler_daemon_state` checkpoint, single-instance lock, decision JSONL log, automatic completed/open-work audit, chronological month-cursor advancement, and service-manager-ready template under `deploy/systemd/`. The service chooses the next month from durable workflow state and the maintained workflow plan; the owner does not tell it where to continue. `scripts/tasks/plan_dataset_expansion.py` provides the explicit dataset-expansion decision surface used by the scheduler policy: plan-only by default, and `--write` prepares only safe artifacts/payloads while preserving provider, promotion, and execution gates. See [`99_historical_scheduler_runtime.md`](99_historical_scheduler_runtime.md) for boot, resume, and maintenance expectations.

## Non-Goals

This policy does not authorize:

- provider dispatch without manager request bounds, resource controls, receipts, and terminal-coverage guardrails;
- production model activation without a script-called agent decision artifact;
- broker execution or account mutation;
- hiding long-running jobs from receipts/artifacts/summary;
- running duplicate scheduler daemons over the same lock/state path;
- saturating the host just because historical backlog exists.
