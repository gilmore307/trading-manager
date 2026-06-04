# Decisions

This is the current decision ledger for `trading-manager`. It records durable active rules.

## D001 - Manager is the control plane

`trading-manager` owns architecture, registry, contracts, request routing, scheduler policy, review gates, promotion gates, shared helpers, and status surfaces. It does not own data production, model implementation, storage execution, dashboard UI, broker execution, generated artifacts, or secrets.

## D002 - Registry rows are current-table synced

Active registry entries live in `scripts/registry/current.csv` and sync into the SQL-backed `trading_registry` table through `scripts/registry/sync_registry.py`. The current table definition is `scripts/registry/sql/trading_registry.sql`; the registry no longer uses stacked `schema_migrations`. Registry `id` is the stable automation reference; `key` is display/search text.

## D003 - Component work is contract-routed

Manager work flows through request, input-binding, run, artifact, ready-signal, and summary contracts. Components perform implementation work and emit receipts. Manager validates whether outputs are acceptable for downstream use.

## D004 - SQL stores durable control-plane facts

Manager SQL stores concise durable facts and references. Large payloads, logs, source files, model artifacts, and dashboard payloads live in storage or runtime paths and are referenced by URI/hash/metadata.

## D005 - Historical modeling is not trading execution

The historical scheduler may acquire data, prepare features, run safe offline stages, prepare replay and attribution requests, and prepare review evidence. It must not place orders, mutate broker/account state, activate production models, or choose the active promoted-model roster.

When future live runtime is enabled, historical model tasks are paused. The
scheduler should select no historical work while realtime trading, market-data
ingestion, broker gates, account freshness, and C08 model-group comparison are
competing for host capacity.

## D006 - The model stack has ten current layers

Manager recognizes the current Layer 1-10 stack: MarketRegime, SectorContext, TargetStateVector, EventFailureRisk, AlphaConfidence, DynamicRiskPolicy, PositionProjection, UnderlyingAction, OptionExpression, and EventRiskGovernor.

## D007 - Reusable foundation catch-up is priority

The scheduler should first advance reusable targetless foundation substrate before ordinary target-specific substrate work. Foundation substrate includes Layer 1 market/cross-asset context, Layer 2 broad sector-anchor and crypto-context evidence, and fold-scoped global or sector-scoped Layer 4 event-observation context. Layer 4 event-observation substrate must be collected for each fold because the accepted event observation pool can change across folds. Valid point-in-time provider data and deterministic features may be reused; dependent replay, attribution, evaluation, and promotion artifacts must be rebuilt when their substrate changes.

Historical training uses the six-month fold as the public first-class work unit across all layers. Months are child partitions inside a fold for data coverage, receipts, and provider batching; they are not separate owner-facing training tasks. Dashboard task identity and stage progress must therefore present Layer 1+ data acquisition, feature generation, model generation, evaluation, and review under the same fold period such as `2016-fold1`. A fold is eligible only after its final calendar month is complete in `America/New_York`; for example `2026-fold1` stays closed until 2026-07-01 because it ends at 2026-06. Public task numbers are list sequence numbers assigned after chronological fold, layer, and workflow-stage sorting; `task_uid` is the durable identity for progress/evidence joins. Worker identity is internal execution detail because one fold can run through multiple provider or ingest lanes; Tasks should not display or filter by worker.

The scheduler must finish one fold's full run cycle before opening the next fold. Completion means Layer 1-9 pre-replay model work, model replay, Layer 10 Event Risk Governor attribution, model evaluation, model promotion, and maintenance/readiness handoff are done. Layer 10 can update the event-observation pool used by later Layer 4 folds, so starting the next fold after Layer 1-9 alone is invalid.

## D008 - Layer 9 is optional trading guidance/expression

Layer 9 may produce optional offline trading-guidance records and option-expression plans from the Layer 8 direct-underlying thesis and point-in-time option context when available. It is not an event-risk governor and does not execute trades or mutate broker/account state.

## D009 - Layer 4 consumes only accepted event-failure evidence

Layer 4 may condition alpha only with evidence packets that passed source precedence, point-in-time availability, non-overlap, matched controls, leakage review, and agent/manager acceptance. Raw anomalies and unreviewed event text cannot enter Layer 4 scoring.

When Layer 10 has not yet produced accepted attribution or promotion evidence,
the Layer 4 event-observation substrate may be empty. That is a valid state:
Layer 4 should materialize a no-event-risk input and downstream scoring should
resolve to `no_reviewed_event_failure_risk` rather than blocking the fold.

C07 provisional untrained-event risk estimates are not Layer 4 inputs. They may
support live trading-review decisions and later Layer 10/Layer 4 promotion
research, but they cannot be treated as trained event-failure evidence until the
normal review and acceptance route completes.

## D010 - Layer 10 remains post-replay residual event-risk governance

Layer 10 governs residual event risk only after concentrated live-flow replay has produced settled replay traces, failures, residuals, misses, or path deviations. It must not run as a pre-replay data-acquisition or feature-generation stage. Layer 9 guidance/expression context is optional attribution context when available; crypto/direct-underlying-only routes must not require option-chain or option-expression refs.

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

Active docs describe current contracts, responsibilities, and operating rules directly. Audit-only details remain in Git history or append-only SQL migrations.

## D016 - Manager writes fold completion state only

Manager writes model-worker fold progress runtime state: fold id, start/end months, stage statuses, and whether all model-worker work is complete. Storage reads that runtime state directly and owns backup, archive, cleanup planning, lifecycle execution, and receipts. Manager must not emit backup/delete signals, requests, or plans for completed folds.

## D017 - Replay Judgment Moves To Evaluation; Runtime Lifecycle Moves To Execution

Offline model-quality judgment after a completed run cycle belongs in `trading-evaluation`, not in manager. Manager records scheduler state and consumes evaluation/execution status, but the replay contract, run settlement, metric semantics, promotion eligibility decision, and promotion readiness record live in the independent evaluation repository.

Runtime promoted-model lifecycle management belongs in `trading-execution`: the active model trades, promoted-but-not-active models run shadow during market hours, ranks 2-4 stay realtime candidates, and weak models enter eliminate-candidate review when sufficient reason evidence exists. Active selection is still separate from broker/order/account mutation.

## D018 - Promotion Waits For Full Run Cycle

Promotion review is not triggered when one model finishes a local check or one target substrate lane completes. Layer-local checks and target-substrate runs remain diagnostic until the candidate bundle has completed the same run cycle.

The current run cycle is reusable foundation substrate, target substrate where needed, live-flow replay, post-replay failure attribution, evaluation, and promotion/lifecycle handoff. Replay must simulate the frozen live component graph over the historical candidate pool with a fixed `25000.0` USD replay initial capital for equity-path diagnostics and return normalization; this is not broker/account state. Components may choose no target, one target, or a target combination. Evaluation compares the pinned candidate bundle against accepted baselines after attribution evidence exists. Promotion acceptance is bundle-scoped: individual layer results are diagnostic and support failure attribution, but no single layer or partial substack can be promoted independently without an accepted component-local lifecycle contract.

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

The candidate policy is rule-fixed: current realtime routing uses the reviewed realtime total-symbol pool, target metadata, current market-wide hot/liquid names, liquidity/spread/data-quality filters, optional optionability diagnostics, and controls when evaluation needs contrast. Promotion replay uses the fixed `historical_candidate_universe.csv` table seeded from the current realtime pool plus BTC, ETH, and SOL, and must not read the mutable realtime pool directly or use current ETF holdings. This fixed table is stable replay scope, not point-in-time historical market-wide ranking evidence. Same-day candidate-universe freezes remain route-smoke evidence until the post-close readiness gate; replay execution must back off before that gate.

Layer 3 and later substrate work may remain target-major in task execution because routing symbols prepare data samples. That scheduling choice does not select the replay target. Promotion replay runs the live-flow component graph over the fixed historical candidate pool, allowing components to choose no target, one target, or a target combination. Fixed target/window panels remain diagnostic repair evidence only and are not accepted promotion evidence.

Historical replay may acquire data that does not already exist locally. That acquisition is replay-owned, month-sharded, budget-gated, and temporary: it materializes only the historical candidate set needed for the shard, records lightweight receipts, coverage, hashes, and decision rows, and deletes transient month-cache inputs after the shard is accepted. Replay must not use preexisting local source directories as the candidate-selection mechanism.

Realtime/live execution is different. It consumes the current provider stream or current provider snapshots through the live component graph and should not pre-download historical source bundles before making decisions. It still records lightweight runtime evidence, provider request metadata, decisions, gates, and fills for audit, replay, and post-trade analysis.

## D213 - Model-worker targets rotate autonomously

Manager may run Layer 3+ historical model-worker training as target-scoped fold chains. Each target owns separate fold checkpoint files, so one completed target does not consume or overwrite another target's `2016-01` onward training state.

When no target is pinned by the service command, the scheduler reads the ordered runtime target queue and selects the first target with an open or unstarted six-month fold. If the current target has completed all eligible folds through the latest fully completed training fold, manager skips it and starts the next target from the earliest ready fold, normally `2016-01`.

The target queue is an execution-routing queue, not promotion evidence and not a replacement for Layer 3 candidate-policy replay. Promotion still requires evaluation-owned replay evidence over the accepted candidate policy.

## D214 - Model group reruns start from the earliest affected workflow cutpoint

Architecture-driven regeneration is a controlled `model_group_rerun_plan`, not an ad hoc repeat of completed tasks.

The plan must identify the earliest affected `layer.stage`, compute all downstream generated outputs and completed workflow state that must be invalidated or lifecycle-classified, preserve unaffected upstream/source evidence, and record reused artifacts in `retained_set` with their controlling root. Source data is protected by default. It may enter the lifecycle candidate set only when the cutpoint is `data_acquisition` and the required source data definition, provider/source parameters, acquisition contract, or existing source partition is itself stale or wrong.

After the candidate/protected/retained sets are accepted, the embedded `storage_lifecycle_request` hands physical artifact treatment to the storage lifecycle pipeline. The reset then invalidates bounded workflow state, writes a durable receipt under the control-plane runtime root, and the single active scheduler reenters from the cutpoint under current contracts. Rerun verification must include contract validation, controlled-root audit, model-output quality checks, lifecycle/evaluation artifacts where applicable, and dashboard/read-model refresh. Physical deletion remains a later storage-owned lifecycle action, not a manager reset action.
