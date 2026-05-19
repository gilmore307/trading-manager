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

## D006 - The model stack has nine current layers

Manager recognizes the current Layer 1-9 stack: MarketRegime, SectorContext, TargetStateVector, EventFailureRisk, AlphaConfidence, PositionProjection, UnderlyingAction, TradingGuidance/OptionExpression, and EventRiskGovernor/EventIntelligenceOverlay.

## D007 - Layer 1/2 foundation catch-up is priority

The scheduler should first advance targetless Layer 1 market/cross-asset and Layer 2 sector/industry substrate before ordinary Layer 3+ target work. Valid point-in-time provider data and deterministic features may be reused; dependent model/evaluation/promotion artifacts must be rebuilt when their substrate changed.

## D008 - Layer 8 is optional trading guidance/expression

Layer 8 may produce optional offline trading-guidance records and option-expression plans from the Layer 7 direct-underlying thesis and point-in-time option context when available. It is not an event-risk governor and does not execute trades or mutate broker/account state.

## D009 - Layer 4 consumes only accepted event-failure evidence

Layer 4 may condition alpha only with evidence packets that passed source precedence, point-in-time availability, non-overlap, matched controls, leakage review, and agent/manager acceptance. Raw anomalies and unreviewed event text cannot enter Layer 4 scoring.

## D010 - Layer 9 remains residual event-risk governance

Layer 9 governs residual event risk over the Layer 7 direct-underlying/spot thesis. Layer 8 guidance/expression context is optional input context when available; crypto/direct-underlying-only routes must not require option-chain or option-expression refs.

## D011 - Promotion activation requires agent decision evidence

A production activation path must reference an accepted `agent_model_promotion_decision`. Advisory reviews, missing reviews, rejected decisions, deferred decisions, or stale artifacts cannot activate production pointers.

## D012 - Storage lifecycle mutation is separately gated

Storage lifecycle decisions require policy evidence, protected-set checks, decision artifacts, and receipts. Historical scheduler progress does not imply permission to delete, archive, or mutate durable storage.

## D013 - Provider calls are explicit gated work

Provider calls require manager request scope, coverage/resource checks, and the explicit dispatch path. Dry-run planning, payload materialization, and handoff validation must not silently call providers.

## D014 - Runtime state is resumable and local by default

Service locks, scheduler state, workflow checkpoints, decision logs, and status summaries live under ignored runtime paths unless intentionally promoted into durable storage. They are operational state, not source docs.

## D015 - Documentation favors current contracts

Active docs should describe the current system from first principles. Obsolete naming, abandoned approaches, and transitional planning notes should be removed from active explanations unless they are necessary to operate current code.

## D016 - Manager writes fold completion state only

Manager writes model-worker fold progress runtime state: fold id, start/end months, stage statuses, and whether all model-worker work is complete. Storage reads that runtime state directly and owns backup, archive, cleanup planning, lifecycle execution, and receipts. Manager must not emit backup/delete signals, requests, or plans for completed folds.

## D017 - Benchmark Judgment Moves To Trading Evaluation

Model-quality judgment after a completed fold belongs in `trading-evaluation`, not in manager. Manager records scheduler state and consumes evaluation status, but the benchmark contract, fold settlement, metric semantics, and promotion eligibility decision live in the independent evaluation repository.

The primary benchmark uses one frozen target/window with training-exclusion proof so fold-to-fold settlement remains comparable. Promotion eligibility is not production activation.

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

Ordinary bar, volume, spread, liquidity, target-state, option-expression, Layer 9 event-risk guidance, strategy-failure label, post-event realized label, or uncalibrated detector payloads cannot be renamed into Layer 9 evidence.
