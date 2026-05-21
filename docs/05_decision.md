# Decisions

This is the current decision ledger for `trading-manager`. It records durable active rules, not every route taken to reach them. Earlier wording remains available in Git history and immutable registry migrations.

## D001 - Manager is the control plane

`trading-manager` owns architecture, registry, contracts, request routing, scheduler policy, review gates, promotion gates, shared helpers, and status surfaces. It does not own data production, model implementation, storage execution, dashboard UI, broker execution, generated artifacts, or secrets.

## D002 - Registry rows are SQL-backed

Active registry entries are created or changed by SQL migrations under `scripts/registry/sql/schema_migrations/`. `scripts/registry/current.csv` is generated evidence and must not be edited by hand. Registry `id` is the stable automation reference; `key` is display/search text.

## D003 - Component work is contract-routed

Manager work flows through request, input-binding, run, artifact, ready-signal, and summary contracts. Components perform implementation work and emit receipts. Manager validates whether outputs are acceptable for downstream use.

## D004 - SQL stores durable control-plane facts

Manager SQL stores concise durable facts and references. Large payloads, logs, source files, model artifacts, and dashboard payloads live in storage or runtime paths and are referenced by URI/hash/metadata.

## D005 - Historical modeling is not trading execution

The historical scheduler may acquire data, prepare features, run safe offline stages, evaluate models, and prepare review evidence. It must not place orders, mutate broker/account state, or activate production models without the accepted promotion path.

## D006 - The model stack has ten current layers

Manager recognizes the current Layer 1-10 stack: MarketRegime, SectorContext, TargetStateVector, EventFailureRisk, AlphaConfidence, DynamicRiskPolicy, PositionProjection, UnderlyingAction, TradingGuidance/OptionExpression, and EventRiskGovernor/EventIntelligenceOverlay.

## D007 - Layer 1/2 foundation catch-up is priority

The scheduler should first advance targetless Layer 1 market/cross-asset and Layer 2 sector/industry substrate before ordinary Layer 3+ target work. Valid point-in-time provider data and deterministic features may be reused; dependent model/evaluation/promotion artifacts must be rebuilt when their substrate changed.

## D008 - Layer 9 is optional trading guidance/expression

Layer 9 may produce optional offline trading-guidance records and option-expression plans from the Layer 8 direct-underlying thesis and point-in-time option context when available. It is not an event-risk governor and does not execute trades or mutate broker/account state.

## D009 - Layer 4 consumes only accepted event-failure evidence

Layer 4 may condition alpha only with evidence packets that passed source precedence, point-in-time availability, non-overlap, matched controls, leakage review, and agent/manager acceptance. Raw anomalies and unreviewed event text cannot enter Layer 4 scoring.

## D010 - Layer 10 remains residual event-risk governance

Layer 10 governs residual event risk over the Layer 8 direct-underlying/spot thesis. Layer 9 guidance/expression context is optional input context when available; crypto/direct-underlying-only routes must not require option-chain or option-expression refs.

## D011 - Agent model review is advisory and blinded

Agent model reviews may support evaluation and execution decisions, but they do not activate production pointers. Offline promotion readiness belongs to `trading-evaluation`; runtime active selection and active pointer writes belong to `trading-execution`.

Any agent that compares models must receive anonymous labels only. It must not know which model is new, old, active, incumbent, champion, challenger, or latest. If identity blinding fails, the review must defer or return insufficient evidence.

## D012 - Storage lifecycle mutation is separately gated

Storage lifecycle decisions require policy evidence, protected-set checks, decision artifacts, and receipts. Historical scheduler progress does not imply permission to delete, archive, or mutate durable storage.

## D018 - Agent decision surfaces require fixed skills

Every agent decision surface must cite a fixed workspace skill so the reviewer uses a stable rubric instead of ad hoc judgment:

- `promotion-evaluation-review` for offline replay and promotion eligibility review.
- `runtime-model-lifecycle-review` for execution-owned active/shadow roster review.
- `event-strategy-promotion-review` for event-family or strategy-failure promotion into model layers.
- `target-context-review` for target-to-Layer-2 context mapping review.
- `failure-register-review` for failed request disposition.
- `server-error-diagnosis` for bounded server error diagnosis and safe repair.
- `storage-lifecycle-review` for backup, cleanup, archive, restore, and delete review.

## D013 - Provider calls are explicit gated work

Provider calls require manager request scope, coverage/resource checks, and the explicit dispatch path. Dry-run planning, payload materialization, and handoff validation must not silently call providers.

## D014 - Runtime state is resumable and local by default

Service locks, scheduler state, workflow checkpoints, decision logs, and status summaries live under ignored runtime paths unless intentionally promoted into durable storage. They are operational state, not source docs.

## D015 - Documentation favors current contracts

Active docs should describe the current system from first principles. Obsolete naming, abandoned approaches, and transitional planning notes should be removed from active explanations unless they are necessary to operate current code.

## D016 - Manager writes fold completion state only

Manager writes model-worker fold progress runtime state: fold id, start/end months, stage statuses, and whether all model-worker work is complete. Storage reads that runtime state directly and owns backup, archive, cleanup planning, lifecycle execution, and receipts. Manager must not emit backup/delete signals, requests, or plans for completed folds.

## D017 - Replay Judgment Moves To Evaluation; Runtime Activation Moves To Execution

Offline model-quality judgment after a completed fold belongs in `trading-evaluation`, not in manager. Manager records scheduler state and consumes evaluation/execution status, but the replay contract, fold settlement, metric semantics, promotion eligibility decision, and promotion readiness record live in the independent evaluation repository.

Runtime active model selection belongs in `trading-execution`: the active model trades, promoted-but-not-active models run shadow during market hours, ranks 2-4 stay realtime candidates, and weak models enter eliminate-candidate review when sufficient reason evidence exists. Active selection is still separate from broker/order/account mutation.

## D018 - Promotion Waits For Full Fold Stack

Promotion review is not triggered when one model finishes one fold. Layer-local fold evaluation remains diagnostic until Layer 1 through Layer 10 have all completed model evaluation for the same fold.

Manager may continue running layer-local generation and evaluation stages as each dependency is ready, but the promotion gate opens only after `fold_layers_01_10_model_evaluation_complete`. Evaluation then replays one pinned Layer 1-10 version bundle through the frozen live-flow component graph, including Layer 10 EventRiskGovernor calls, and compares it against accepted baselines. Promotion acceptance is all-or-nothing for that bundle: individual layer results are diagnostic and support failure attribution, but no single layer or partial substack can be promoted independently.

## D210 - Activity bridge non-overlap is mandatory

Activity bridge evidence must prove one of these statuses before it can affect scoring or intervention:

```text
not_in_upstream_features
residual_after_upstream_conditioning
review_required_overlap_unknown
```

Only `not_in_upstream_features` and `residual_after_upstream_conditioning` may support scoring, intervention, or Layer 4 promotion. `review_required_overlap_unknown` is review/provenance only.

## D211 - Startup abnormality scope is narrow

Layer 9 / Activity Bridge startup abnormality evidence is limited to compact point-in-time detector references in these families:

```text
price_action_pattern
residual_market_structure_disturbance
microstructure_liquidity_disruption
option_derivatives_abnormality
```

Ordinary bar, volume, spread, liquidity, target-state, option-expression, Layer 10 event-risk guidance, strategy-failure label, post-event realized label, or uncalibrated detector payloads cannot be renamed into Layer 9 evidence.

## D212 - Layer 3 candidate selection is policy-based

Layer 3 candidate selection is part of the model stack, not an externally preselected final ticker list. Manager recognizes Layer 3 as an anonymous target-state model that may rank the current candidate-policy batch for target handoff.

The candidate policy is rule-fixed: current Layer 2 selected/watch sectors, reviewed sector constituents or proxies, current market-wide hot/liquid names, liquidity/spread/data-quality filters, optional optionability diagnostics, and controls when evaluation needs contrast.

Layer 3 work may remain target-major in task execution because routing symbols only contribute anonymous samples. Layer 4 and later remain single-target interfaces: if Layer 3 hands off multiple ranked targets, manager schedules separate target-scoped workflow runs instead of passing a multi-target batch into Layer 4+. Promotion evidence must still aggregate by fold and candidate-policy batch. Ordinary promotion replay uses the canonical candidate-policy replay window `2021-01-01` through `2026-01-01` end-exclusive; fixed target/window panels are not accepted promotion evidence.

## D213 - Model-worker targets rotate autonomously

Manager may run Layer 3+ historical model-worker training as target-scoped fold chains. Each target owns separate fold checkpoint files, so one completed target does not consume or overwrite another target's `2016-01` onward training state.

When no target is pinned by the service command, the scheduler reads the ordered runtime target queue and selects the first target with an open or unstarted six-month fold. If the current target has completed all eligible folds through the latest completed calendar month, manager skips it and starts the next target from the earliest ready fold, normally `2016-01`.

The target queue is an execution-routing queue, not promotion evidence and not a replacement for Layer 3 candidate-policy replay. Promotion still requires evaluation-owned replay evidence over the accepted candidate policy.
