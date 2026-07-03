# Task System

The task system is the manager control-plane lifecycle for component work.

## Lifecycle

```text
1. Manager creates or previews a request.
2. Manager materializes parameter/input payloads by reference.
3. Manager validates the handoff boundary.
4. A component performs work.
5. The component emits a completion receipt.
6. Manager normalizes run/artifact/ready rows.
7. Manager surfaces task summary, failure evidence, and next action.
```

## Core Rows

- `manager_request` — requested work.
- `input_binding` — approved input refs.
- `run_manifest` — component run summary.
- `run_step` — optional step detail.
- `artifact_ref` — output refs.
- `ready_signal` — declared readiness for a consumer scope.
- `task_summary` — derived read model; it does not own state.

## Priority Values

```text
critical | high | normal | low | backlog
```

Default priority is `normal`. Summary ordering is priority, deadline, created time, then request id.

## Failure Handling

Failures should become durable evidence, not chat-only notes. Ordinary runtime, provider, and stage failures route through automatic diagnosis, repair, retry, and reconciliation. Promotion, storage lifecycle, and trading decisions are automatic evidence/control gates, not human or agent `review_required` gates. Human intervention is reserved for development-route or contract changes, legal/platform/tool blockers, explicit live broker/account/order authority changes, or irreversible destructive actions outside an accepted automatic lifecycle policy. The Codex error-repair runner uses `danger-full-access` so the `server-error-repair` closed-loop contract can commit/push maintained fixes and rerun internal database-backed stages; the prompt boundary still forbids broker/account/order/fill/position mutation and secret exposure.

## Safety Gates

- Planning and materialization are safe by default.
- Provider calls require explicit provider dispatch.
- Runtime model lifecycle requests require accepted promotion or shadow-cycle evidence.
- Manager must not activate production pointers directly.
- Storage lifecycle mutation requires accepted lifecycle decision.
- Broker/account mutation is not allowed in manager.
- Live-enabled provider runtime task keys are execution scratch. The canonical prepared source task key remains under its request path; successful provider dispatch removes the runtime copy after the subprocess consumes it, while failed dispatch retains the runtime copy for diagnosis.

## Model Research Run Cycle

Model research tasks are grouped by data reuse and decision-cycle ownership, not
by the retired serial loop.

All model tasks share the same lifecycle stage semantics: data acquisition,
feature or evidence generation, model generation, evaluation, promotion or
shadow handoff, and runtime monitoring. A model group may declare domain-specific
source contracts, label contracts, feature/evidence contracts, gate contracts,
and not-applicable states, but it must not define a separate orchestration
meaning for these stages. Manager owns the state machine, gap discovery,
provider-dispatch boundary, retry/stop routing, point-in-time/leakage gates, and
ready-state projection across all model groups. Event-family modelability follows
these conventions inside M03 event-state generation, while replay review owns
post-replay event attribution as an embedded diagnostic surface.

Model rows and labels use the shared label-settlement contract in
`docs/03_contracts.md`. A row belongs to a split by its observed or decision
time. Forward outcome labels may settle after that split when the declared
horizon requires later market data. Such labels are usable only when
`label_available_at` is on or before the relevant `training_cutoff`; leakage
checks must audit feature availability and label availability instead of
dropping all split-boundary rows.

The public task list is a task-fact projection over scheduler state. It shows
completed history, failures, and one current executable or review task. Future
blocked stages remain internal workflow dependencies and must not appear as
independent Tasks rows. When the current task is fold-scoped, its month
coverage remains child partition evidence under that one task.

The historical workflow transition ledger is the task system's current-owner
surface. Scheduler lane selection, stage readiness, execution, waits, terminal
outcomes, and failures all flow through
`runtime/historical_workflow_transitions.jsonl`; the latest row replaces
`runtime/historical_workflow_transition_latest.json`. Dashboard, status, and
repair consumers read that latest transition before consulting detailed
workflow checkpoints, decision logs, receipts, or read-model projections.
Checkpoint files own stage detail, but they do not own the current task.

Autonomous model-worker training is target-scoped. It may select only reviewed
optionable equity targets from the runtime target queue; structurally
non-optionable assets such as crypto spot may remain in replay/context universes
but do not open M02-M05 training folds. When no legal target is available, the
model-worker lane has no owner instead of falling back to a targetless fold.

1. Foundation substrate. Build reusable M01 background-context source/feature
   evidence and fold-scoped M03 event-impact inputs. M03 collects the full
   point-in-time fold event universe, runs event-family modelability and impact
   evidence gates, and may emit a no-event-risk state when the fold has no
   admissible event-impact evidence. Event-feed coverage checks are shared
   source plumbing only; feed rows are not M03 event-state evidence until they
   pass the M03 event-impact gate.
2. Target substrate. Ordinary replay materializes M02 target-state source and
   feature evidence from the fixed `historical_candidate_universe.csv` candidate
   pool. If a requested diagnostic target lacks reviewed target-local bar
   artifacts for a fold, manager prepares bounded `01_feed_alpaca_bars` requests
   for that target and dispatches them through the autonomous provider gate. The
   existing `m03_target_state_vector_data_acquisition` materializer remains the
   migration-source implementation detail consumed by current M02.
3. Option-expression substrate. For targets whose metadata leaves listed
   options applicable, manager prepares `trading_data.option_chain_state_source`
   under the M05 option-expression stage
   `model_05_option_expression.option_chain_data_acquisition`. Crypto and
   confirmed no-listed-options targets skip the option source/feature stages but
   still retain M05 model-generation stages so the model can learn and emit
   no-option/not-applicable states.
4. Live-flow replay. Replay simulates the real system under a historical
   point-in-time background. Components may scan the eligible candidate pool,
   choose no target, choose one target, or choose a target combination. Replay
   must not be framed as "run this already selected symbol through the stack"
   unless the request is an explicit diagnostic repair scenario.
5. Replay review. Replay review owns the first post-replay component-funnel
   review over missed winners, bad fills, target-selection misses,
   overblock/underblock behavior, option-expression drag, and event attribution.
   It consumes the fixed pre-replay M03 event ledger and writes event-attribution
   subartifacts inside the replay review run. It must not acquire provider data,
   mutate the M03 ledger, or open a separate M06 scheduler stage.
6. Event-family modelability acquisition and evidence generation. When M03 must
   judge whether an event family can be described by an impact probability
   function, it uses the shared model-task lifecycle vocabulary: acquisition
   materializes bounded PIT event inputs, feature/evidence generation builds
   deterministic modelability gate inputs, and semantic review runs only after
   program gates make the packet admissible. It first creates a
   `model_06_event_family_modelability_acquisition_plan`. The plan declares the
   concrete event-family seed, same-family sample threshold, required canonical
   feeds, PIT window, and provider task keys. Source/category buckets such as
   `news`, `target_news_or_disclosure`, `scheduled_macro_release`, and `macro`
   are not valid event families; they must be narrowed to families such as
   `target_product_price_change_news`, `target_product_launch_news`,
   `target_supply_chain_disruption_news`, `target_regulatory_antitrust_news`,
   `cpi_release`, or `ppi_release`. M03 uses a hierarchical event ontology:
   source/category and domain nodes support routing and priors, mechanism
   families are the default modelability unit, and reviewed child families or
   specific dossiers can specialize recurring entity/theme behavior. Tickers,
   issuers, sectors, and dates are observation labels, acquisition filters, or
   dossier refs until reviewed evidence promotes a narrower child/dossier.
   Provider calls remain in the reviewed dispatcher. After acquisition, code
   builds `model_06_event_family_modelability_evidence_packet` from acquired
   same-family PIT observations. The packet must pass deterministic
   admissibility gates before Codex modelability review; mixed-family packets,
   packets missing structured event parameters, and packets missing
   controls/calibration remain blocked instead of being relabeled as
   context-only. The next-action runner consumes the packet readiness state and
   writes the next program-owned route artifact: acquisition task keys,
   structured evidence enrichment plan, modelability-gate evidence-generation
   plan, or semantic review handoff. Codex review consumes only admissible
   semantic-review handoffs and performs no provider calls. Program gates own
   coverage, dedupe, overlap/confounder checks, stop/retry conditions, and
   review readiness; agents only perform semantic review that deterministic code
   cannot reliably encode. A single event cannot establish the family function
   type.
8. Evaluation. Evaluation consumes replay traces, replay-review rows, and attribution packets to
   score the candidate component bundle against baselines, calibration,
   stability, leakage, portfolio behavior, and failure explanations.
9. Promotion and lifecycle handoff. Promotion produces accepted/rejected/deferred
   evidence for a model bundle. Management of already promoted models belongs to
   the runtime component lifecycle owner, not to manager activation.

The manager schedules and records these tasks. It does not turn a historical
target-substrate request into a fixed-target strategy claim, and it does not
activate promoted models directly.

## Trading Economics calendar maintenance

Trading Economics calendar handling has one accepted source route:

1. Canonical source: reviewed TE calendar CSV/JSONL rows under `trading-storage/storage/01_source_data/monthly_backfill/trading_economics_calendar_web/YYYY-MM/runs/<run_id>/`. These files are append-only protected and Git-recoverable.
2. Derived materializations: SQL rows, control-plane filtered artifacts, and dashboard read models are rebuildable operational/materialized state, not the source of truth. TE macro rows should stay out of dashboard event markers and replay-review attribution until the accepted M03 event-state route admits the macro event family into the event-risk/attention pool.

Manager workflows may schedule the bounded recent/future Trading Economics calendar refresh into canonical storage source rows. They must not record TE website URLs as source references, write TE receipts/manifests/diagnostics/schemas into source storage, write TE macro rows into residual-event compatibility materializations, or silently merge public web-search fallback rows into TE-origin source data.

TE refresh creates normal daily Git changes in the canonical source-data tree. Maintenance commits should include those changed/new TE source files with the code or docs batch when they are relevant to the same acceptance window; their presence in `git status` is not a cleanup problem. Rerun resets must preserve these files, record the TE root in `protected_set`/`retained_set`, and never delete TE canonical source data.

## Useful Commands

```bash
PYTHONPATH=src python3 scripts/tasks/submit_manager_requests.py requests.jsonl
PYTHONPATH=src python3 scripts/tasks/materialize_request_payloads.py requests.jsonl --write-files
PYTHONPATH=src python3 scripts/tasks/validate_request_handoff.py --from-db --request-id mgrreq_example
PYTHONPATH=src python3 scripts/tasks/record_completion_receipt.py completion_receipt.json --request-id mgrreq_example --component-id component --repo-id trading-data --receipt-uri storage://example/receipt.json
PYTHONPATH=src python3 scripts/tasks/list_task_summary.py --limit 50
PYTHONPATH=src python3 scripts/tasks/rehearse_task_system.py --end-month 2016-01 --limit 3 --scenario mixed --format jsonl
# Retired/inventory only; does not create source_06 task keys.
PYTHONPATH=src python3 scripts/tasks/plan_trading_economics_calendar.py historical-seed --start-month 2016-01 --end-month 2026-05
```
