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

## D006 - The manager model stack has five pre-replay models

Manager recognizes the current pre-replay model stack as M01 BackgroundContext, M02 TargetState, M03 EventState, M04 UnifiedDecision, and M05 OptionExpression. Former M06 residual-event functions are no longer an independent model/task lane; their useful event-attribution role is embedded in replay review.

## D006A - Model tasks share lifecycle stage semantics

All model groups use the same model-task lifecycle vocabulary: data acquisition, feature or evidence generation, model generation, evaluation, promotion or shadow handoff, and runtime monitoring. Model groups may declare different domain contracts for sources, clocks, labels, features, gates, and not-applicable states, but they must not create separate orchestration semantics for the same lifecycle responsibilities.

Manager owns the lifecycle state machine, gap discovery, provider-dispatch boundary, retry/stop routing, artifact references, point-in-time/leakage gates, and readiness projection. Model-group code owns domain-specific implementation behind those declared contracts. M03 owns the pre-replay event-universe and event-impact lifecycle stages. Replay review owns post-replay event attribution as a diagnostic sub-surface, not as a separate model lifecycle.

## D007 - Reusable foundation catch-up is priority

The scheduler should first advance reusable targetless foundation substrate before ordinary target-specific substrate work. Foundation substrate includes M01 market/cross-asset context, M02 broad sector-anchor and crypto-context evidence, and fold-scoped global or sector-scoped M03 event-observation context. M03 event-impact substrate must be collected for each fold because the accepted event observation pool can change across folds. Valid point-in-time provider data and deterministic features may be reused; dependent replay, attribution, evaluation, and promotion artifacts must be rebuilt when their substrate changes.

Historical training uses the 18-month `12+3+3` cumulative walk-forward fold as the public first-class work unit across all layers. Current fold ids use the training data source and training year, such as `fold_aapl_2016`; the window range `2016-01..2017-06` is coverage evidence, not the business fold name. Months are child partitions inside a fold for data coverage, receipts, and provider batching; they are not separate owner-facing training tasks. Dashboard task identity and stage progress must therefore present M01+ data acquisition, feature generation, model generation, evaluation, and review under the same fold period. A fold is eligible only after its final test-window calendar month is complete in `America/New_York`; the `fold_aapl_2016` window cannot open before `2017-07-01` because it needs data through 2017-06. Public task numbers are list sequence numbers assigned after chronological fold, layer, and workflow-stage sorting; `task_uid` is the durable identity for progress/evidence joins. Historical runtime advances one canonical month at a time; worker identity is internal execution detail and Tasks should not display or filter by worker. For overlapping January-June substrate months, public task ownership stays with the earliest open training-year fold that contains the month; `2024-01` through `2024-06` cannot display or run as `fold_aapl_2024` while `fold_aapl_2023` is still open. Pre-replay model work includes a fold-scoped cumulative replay-entry checkpoint. The first fold may cold start; each later fold must continue from the immediately previous fold checkpoint and add the next 12 training months before replay admission.

The scheduler must finish one fold's full run cycle before opening the next fold. Completion means M01-M05 pre-replay model work, model replay, replay review with event attribution, model evaluation, model promotion, and maintenance/readiness handoff are done. M03 event-impact changes can update the event-observation pool used by later folds, so starting the next fold after pre-replay model generation alone is still invalid.

## D008 - M05 is optional trading guidance/expression

M05 may produce optional offline trading-guidance records and option-expression plans from the M04 direct-underlying thesis and point-in-time option context when available. It is not an event-risk governor and does not execute trades or mutate broker/account state.

## D009 - M03 owns pre-replay event impact

M03 event-state owns the fold-scoped point-in-time event universe before replay. It materializes reviewed event observations, deterministic calendar/session events, structured event-family evidence, modelability gates, and event-impact projection inputs for the full fold rather than waiting for later model failures. M03 trains and applies point-in-time impact-state projections for events that pass deterministic coverage, control, leakage, overlap, label, and calibration gates.

M03 event taxonomy is hierarchical. Coarse source/category and domain nodes may
support routing and priors for first-seen or low-evidence events, but
modelability packets use the narrowest accepted PIT-definable mechanism family,
child family, or specific event dossier. Fine dossiers such as entity/theme
earnings profiles may override ancestor priors only after reviewed evidence
establishes reusable inclusion/exclusion rules, controls, lineage, and fallback
behavior; hindsight market reaction alone cannot create a taxonomy split.

M03 may materialize a no-event state only when the full fold event-universe route has validly found no reviewed event observations or no admissible event-impact evidence. It must not use selected replay trades, replay failures, post-fold outcomes, or replay-review attribution rows to decide which upstream event rows exist.

C07 provisional untrained-event risk estimates are not M03 event-state inputs. They may
support live trading-review decisions and later M03 event-state promotion
research, but they cannot be treated as trained event-failure evidence until the
normal review and acceptance route completes.

## D010 - Replay review owns post-replay event attribution

Replay review governs post-replay event attribution only after concentrated live-flow replay has produced settled replay traces, failures, residuals, misses, or path deviations. It consumes replay-review evidence plus the fixed pre-replay M03 event-impact ledger to explain residual failures, missed events, overblocks, underblocks, and path deviations. It must not own pre-replay event-universe discovery, event-family modelability gates, event-impact training, provider acquisition, or a separate M06 scheduler stage. M05 guidance/expression context is optional attribution context when available; crypto/direct-underlying-only routes must not require option-chain or option-expression refs.

## D011 - Agent model review is advisory and blinded

Agent model reviews may support evaluation and execution decisions, but they do not activate production pointers. Offline promotion readiness belongs to `trading-evaluation`; runtime active selection and active pointer writes belong to `trading-execution`.

Any agent that compares models must receive anonymous labels only. It must not know which model is new, old, active, incumbent, champion, challenger, or latest. If identity blinding fails, the review must defer or return insufficient evidence.

## D012 - Storage lifecycle mutation is separately gated

Storage lifecycle decisions require policy evidence, protected-set checks, decision artifacts, and receipts. Historical scheduler progress does not imply permission to delete, archive, or mutate durable storage.

## D018 - Agent decision surfaces require fixed skills

Every agent decision surface must cite a fixed workspace skill so the reviewer uses a stable rubric instead of ad hoc judgment:

- `promotion-evaluation-review` for offline replay and promotion eligibility review.
- `runtime-model-lifecycle-review` for execution-owned active/shadow roster review.
- `event-strategy-promotion-review` for event-family or strategy-failure promotion into models.
- `target-context-review` for target-to-M02 context mapping review.
- `failure-register-review` for failed request disposition.
- `server-error-diagnosis` for bounded server error diagnosis and safe repair.
- `storage-lifecycle-review` for backup, cleanup, archive, restore, and delete review.

## D013 - Provider calls are explicit gated work

Provider calls require manager request scope, coverage/resource checks, and the explicit dispatch path. Dry-run planning, payload materialization, and handoff validation must not silently call providers.

## D014 - Runtime state is resumable and local by default

Service locks, scheduler state, workflow checkpoints, decision logs, workflow transition ledgers, and status summaries live under ignored runtime paths unless intentionally promoted into durable storage. They are operational state, not source docs.

The scheduler's workflow transition ledger is the canonical current-transition
surface for dashboard/status/repair consumers. Decision logs remain audit tails;
workflow checkpoint files remain detailed state for scheduler execution; neither
should override a current transition row when reporting active work, terminal
state, failure, target/fold scope, or next action.

## D015 - Documentation favors current contracts

Active docs describe current contracts, responsibilities, and operating rules directly. Audit-only details remain in Git history or append-only SQL migrations.

## D016 - Manager writes fold completion state only

Manager writes model-worker fold progress runtime state: fold id, start/end months, stage statuses, and whether all model-worker work is complete. Storage reads that runtime state directly and owns backup, archive, cleanup planning, lifecycle execution, and receipts. Manager must not emit backup/delete signals, requests, or plans for completed folds.

## D017 - Replay Judgment Moves To Evaluation; Runtime Lifecycle Moves To Execution

Offline model-quality judgment after a completed run cycle belongs in `trading-evaluation`, not in manager. Manager records scheduler state and consumes evaluation/execution status, but the replay contract, run settlement, metric semantics, promotion eligibility decision, and promotion readiness record live in the independent evaluation repository.

Runtime promoted-model lifecycle management belongs in `trading-execution`: the active model trades, promoted-but-not-active models run shadow during market hours, ranks 2-4 stay realtime candidates, and weak models enter eliminate-candidate review when sufficient reason evidence exists. Active selection is still separate from broker/order/account mutation.

## D018 - Promotion Waits For Full Run Cycle

Promotion review is not triggered when one model finishes a local check or one target substrate lane completes. Model-local checks and target-substrate runs remain diagnostic until the candidate bundle has completed the same run cycle.

The current run cycle is reusable foundation substrate, target substrate where needed, live-flow replay, replay review with event attribution, evaluation, and promotion/lifecycle handoff. Replay must simulate the frozen live component graph over the historical candidate pool with a fixed `25000.0` USD replay initial capital for equity-path diagnostics and return normalization; this is not broker/account state. Components may choose no target, one target, or a target combination. Replay review is the first post-replay task: it compares decisions against replay-derived missed/failure evidence, prepares component-funnel review rows, and performs event attribution against the fixed M03 event ledger. Evaluation compares the pinned candidate bundle against accepted baselines after attribution evidence exists. Promotion acceptance is bundle-scoped: individual layer results are diagnostic and support failure attribution, but no single layer or partial substack can be promoted independently without an accepted component-local lifecycle contract.

Equity/options replay uses five simultaneous risk slots by default, each based on a `0.20` model-owned target allocation fraction. Replay keeps scanning after cash or slots are committed and may replace the weakest held position when the new candidate is point-in-time executable, allocation-compatible, and clears the score-scale-aware switch threshold. Receipts using the old fixed `0.05` switch threshold are stale and not current replay evidence.

## D019 - Training, Replay, And Realtime Share Model-Input Semantics

Training, replay, and realtime trading must resolve model decision inputs
through the same declared semantic families, registry terms, feature/vector
definitions, point-in-time clock rules, freshness/quality rules, fallback states,
and governance status. They may use different physical artifacts: training uses
historical source/feature artifacts, replay uses frozen historical snapshots
plus bounded on-demand replay cache, and realtime uses current provider/context
refs. Those physical routes are valid only when they map back to the same model
input contract.

This rule is owned by `docs/29_train_replay_realtime_input_parity.md`. It does
not make broker/account guardrails, halt checks, restrictions, or emergency
kill-switches trained model inputs. Untrained realtime event/calendar context
may support advisory C07/trading-review evidence, but it cannot become M03/M04
model input or automatic live trading action until accepted through the M03
event-impact governance route.

## D210 - Activity bridge non-overlap is mandatory

Activity bridge evidence must prove one of these statuses before it can affect scoring or intervention:

```text
not_in_upstream_features
residual_after_upstream_conditioning
review_required_overlap_unknown
```

Only `not_in_upstream_features` and `residual_after_upstream_conditioning` may support scoring, intervention, or M03 event-state promotion. `review_required_overlap_unknown` is review/provenance only.

## D211 - Startup abnormality scope is narrow

M05 / Activity Bridge startup abnormality evidence is limited to compact point-in-time detector references in these families:

```text
price_action_pattern
residual_market_structure_disturbance
microstructure_liquidity_disruption
option_derivatives_abnormality
```

Ordinary bar, volume, spread, liquidity, target-state, option-expression, M03 event-impact guidance, strategy-failure label, post-event realized label, or uncalibrated detector payloads cannot be renamed into M05 evidence.

## D212 - M02 candidate selection is policy-based

M02 candidate selection is part of the model stack, not an externally preselected final ticker list. Manager recognizes M02 as an anonymous target-state model that may rank the current candidate-policy batch for target handoff.

The candidate policy is rule-fixed: current realtime routing uses the reviewed realtime total-symbol pool, target metadata, current market-wide hot/liquid names, liquidity/spread/data-quality filters, optionability diagnostics, and controls when evaluation needs contrast. Promotion replay uses the fixed `historical_candidate_universe.csv` table seeded from the current realtime equity pool plus the reviewed crypto spot candidate pool, and must not read the mutable realtime pool directly or use current ETF holdings. This fixed table is stable replay scope, not point-in-time historical market-wide ranking evidence. Same-day candidate-universe freezes remain route-smoke evidence until the post-close readiness gate; replay execution must back off before that gate.

M02 and later substrate work may remain target-major in task execution because routing symbols prepare data samples. That scheduling choice does not select the replay target. Promotion replay runs the live-flow component graph over the fixed historical candidate pool, allowing components to choose no target, one target, or a target combination. Fixed target/window panels remain diagnostic repair evidence only and are not accepted promotion evidence.

Historical replay and historical training share canonical reusable source data under `trading-storage/storage/01_source_data`. Replay coverage scans must reuse valid existing source partitions and acquire only missing canonical partitions; replay must not redownload or save duplicate private source bundles for the same 2021-2026 provider/source/month scope. Candidate selection remains governed by the fixed replay candidate universe and point-in-time component graph, not by whichever source directories happen to exist locally. Replay-owned artifacts should be lightweight manifests, coverage rows, receipts, hashes, decisions, and review outputs. Model-specific replay downloads that cannot become reusable source partitions remain temporary and enter cleanup after replay close.

Realtime/live execution is different. It consumes the current provider stream or current provider snapshots through the live component graph and should not pre-download historical source bundles before making decisions. It still records lightweight runtime evidence, provider request metadata, decisions, gates, and fills for audit, replay, and post-trade analysis.

## D213 - Model-worker targets rotate autonomously

Manager may run M02+ historical model-worker training as target-scoped fold chains. Each target owns separate fold checkpoint files, so one completed target does not consume or overwrite another target's `2016-01` onward training state.

When no target is pinned by the service command, the scheduler reads the ordered runtime target queue and selects the first target with an open or unstarted 12+3+3 walk-forward fold. If the current target has completed all eligible folds through the latest fully completed training fold, manager skips it and starts the next target from the earliest ready fold, normally `2016-01`.

The target queue is an explicit execution-routing queue, not promotion evidence and not a replacement for M02 candidate-policy replay. Accepted target-context mappings validate requested queue entries but are not auto-added as training targets. The model-worker queue admits reviewed optionable equity targets only. Crypto spot and other structurally non-optionable symbols may remain in replay/context universes, but they do not enter autonomous model-worker training because they cannot exercise the option-expression surface. Promotion still requires evaluation-owned replay evidence over the accepted candidate policy and option-availability metric slices.

## D214 - Model group reruns start from the earliest affected workflow cutpoint

Architecture-driven regeneration is a controlled `model_group_rerun_plan`, not an ad hoc repeat of completed tasks.

The plan must identify the earliest affected `layer.stage`, compute all downstream generated outputs and completed workflow state that must be invalidated or lifecycle-classified, preserve unaffected upstream/source evidence, and record reused artifacts in `retained_set` with their controlling root. Source data is protected by default. It may enter the lifecycle candidate set only when the cutpoint is `data_acquisition` and the required source data definition, provider/source parameters, acquisition contract, or existing source partition is itself stale or wrong.

After the candidate/protected/retained sets are accepted, the embedded `storage_lifecycle_request` hands physical artifact treatment to the storage lifecycle pipeline. The reset then invalidates bounded workflow state, writes a durable receipt under the control-plane runtime root, and the single active scheduler reenters from the cutpoint under current contracts. Rerun verification must include contract validation, controlled-root audit, model-output quality checks, lifecycle/evaluation artifacts where applicable, and dashboard/read-model refresh. Physical deletion remains a later storage-owned lifecycle action, not a manager reset action.

## D215 - Model labels settle after row ownership

Historical model rows belong to a fold or split by the time they were observed
or the decision would have been made. Future outcome labels are acquired by the
declared horizon and may require market data after the row's split or fold
window. Boundary rows must not be dropped merely because their labels settle in
a later calendar window.

Every model group must separate row ownership, feature availability, label
settlement, and training eligibility. A label can train or evaluate a model only
when `label_available_at` is on or before that run's `training_cutoff`. Leakage
checks must audit `feature_available_at` and `label_available_at`; they must not
replace this timing evidence with a blanket ban on labels that cross a split
boundary.

## D216 - Fold maintenance keeps reusable foundation data and removes side products

Fold maintenance must use the fixed data-disposition matrix in
`docs/03_contracts.md`. Artifact disposition is assigned when an artifact is
created, not guessed at fold close from path names.

M01 background/context source, feature, manifest, and model artifacts are
reusable foundation substrate for future targets and must not be deleted merely
because a target fold completed. Canonical shared source data is likewise
protected.

Replay input data is also shared substrate. The 2021-2026 replay window uses
background/context, event, calendar/session, market-control, and candidate
universe source refs across every fold's replay. These inputs must be stored
once in canonical shared/source locations and referenced by fold replay
manifests rather than duplicated per fold. If a completed fold's cleanup pass
finds data that replay or another fold still cites, maintenance must retain the
canonical copy and delete only duplicate fold-local copies.

Market bars use one shared canonical bars store. Granularity, provider, symbol,
adjustment policy, PIT clock, cleaning status, and calendar window are fields or
partition/query constraints in that store, not separate per-fold payloads. A fold
or replay consumer should store refs to the rows/partitions it used rather than
private copies of the same bars.

Progress-monitoring side products are not durable evidence. After fold
settlement, manager/storage retain only the minimum receipts, transition
summaries, counters, hashes, and error refs needed for audit and repair; the
remaining stage heartbeats, row-progress snapshots, transient debug traces, and
repeated operation manifests enter direct cleanup or rolling retention.

Fold-scoped branch files acquired only to complete a task are disposable once
their consumer evidence is retained and no active consumer still needs the
payload. For example, NVDA data temporarily fetched inside an AAPL fold for
event-scope controls, peer comparison, or replay diagnostics may be deleted
after provenance, dependency reason, coverage summary, hashes, and result refs
are retained only if it was not promoted into canonical shared source coverage
and is not cited by replay or another fold. If that NVDA partition is canonical
or replay-consumed, it is protected and reused instead of being deleted.
