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
but do not open M02-M06 training folds. When no legal target is available, the
model-worker lane has no owner instead of falling back to a targetless fold.

1. Foundation substrate. Build reusable M01 background-context source/feature
   evidence and fold-scoped M03 event-state observation inputs. M03 event
   substrate is collected per fold because M06-governed event-family attributes
   and accepted event-observation pools can change across folds. Event-feed
   coverage checks are shared source plumbing only; feed rows are not M03
   event-state evidence until accepted event-family evidence exists.
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
   overblock/underblock behavior, and option-expression drag. It prepares
   replay-review rows for M06 and evaluation, but it is not event attribution.
6. Residual event governance. M06 owns residual event intervention,
   overblock/underblock, missed-event, and underlying-vs-option failure
   attribution after M04/M05 thesis formation. Its event-family attributes are
   applied by M03 and passed through to M04/M05 as state, but M06 itself is not a
   pre-replay provider data-acquisition lane. When M06 needs local event inputs,
   scheduler may backfill bounded event feeds only after replay review exposes
   the post-replay attribution requirement.
7. Event-family modelability acquisition. When M06 must judge whether an event
   family can be described by an impact probability function, it first creates a
   `model_06_event_family_modelability_acquisition_plan`. The plan declares the
   event-family seed, same-family sample threshold, required canonical feeds,
   PIT window, and provider task keys. Provider calls remain in the reviewed
   dispatcher; Codex modelability review consumes only the acquired evidence
   packet. A single event cannot establish the family function type.
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

1. Canonical source: reviewed TE calendar payloads under `trading-storage/storage/01_source_data/monthly_backfill/trading_economics_calendar_web/YYYY-MM/runs/<run_id>/`. These files are append-only protected and Git-recoverable.
2. Derived materializations: SQL rows, runtime receipts, control-plane filtered artifacts, and dashboard read models are rebuildable operational/materialized state, not the source of truth. TE macro rows should stay out of residual-event governance materializations and dashboard event markers until the accepted M06/event-governance route promotes macro events into the event-risk/attention pool.

Manager workflows may schedule the bounded recent/future Trading Economics calendar refresh into canonical storage source rows. They must not record TE website URLs as source references, must not write TE macro rows into `model_06_residual_event_governance_data_acquisition`, and must not silently merge public web-search fallback rows into TE-origin source data.

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
