# Model Promotion And Lifecycle Scheduling

Manager owns scheduling and request preparation for model promotion/evaluation work. Replay judgment, promotion eligibility, and promotion readiness belong to `trading-evaluation`; runtime active/shadow model selection belongs to `trading-execution`.

When Codex CLI is used for promotion judgment, the request must require the workspace skill `skills/codex/promotion-evaluation-review`. The review is advisory evidence only; `trading-evaluation` deterministic checks own eligibility and readiness records.

## Research-Cycle Gate

Promotion is run-cycle scoped, not single-model or fixed-target scoped. A layer may finish local model generation checks, but that evidence remains diagnostic until the candidate bundle has passed the full historical live-flow cycle:

- reusable foundation substrate;
- target-specific substrate where needed;
- live-flow replay where components freely select no target, one target, or a target combination from the eligible historical pool;
- post-replay failure attribution;
- evaluation against accepted baselines and lifecycle thresholds.

Manager must not schedule promotion review from a single layer's completed fold alone, and it must not convert a target-substrate task into evidence that the system was forced to trade that target. Replay judgment belongs to the frozen live-flow component graph under point-in-time historical evidence.

Promotion acceptance is bundle-scoped. Layer-local evidence remains available for diagnostics, regression attribution, and retraining priority, but it must not create independent promotion, shadow, live, or reusable-production acceptance for a single layer or partial substack unless an accepted lifecycle contract explicitly defines that component-local role.

## Required Evidence

A promotion packet should identify:

- model/layer/candidate refs;
- dataset snapshot and split refs;
- replay candidate-pool and component-selection refs;
- labels and evaluation refs;
- post-replay failure-attribution refs;
- baseline comparisons;
- leakage checks;
- stability and sample-size evidence;
- four replay scorecards: Ranking / Calibration, Selection Quality, Economic Quality, and Slices;
- disagreement report entries where ranking, selection, and economic evidence conflict, such as AUROC below the old diagnostic threshold while excess utility is positive, or AUROC passing while excess return is negative;
- known failure modes;
- downstream shadow/activation scope;
- evaluation decision evidence.
- evidence that the candidate component bundle completed the same replay/evaluation cycle.
- pinned version refs for all component models in the candidate bundle.

## Activation Boundary

Manager must not activate production pointers or manage the active promoted-model roster directly. Offline promotion requires `trading-evaluation` evidence: accepted replay settlement, post-replay failure attribution, `promotion_eligibility_decision`, `promotion_readiness_record`, and rollback/config refs.

Runtime management of already promoted models belongs to the runtime component lifecycle owner. That component compares active, shadow, realtime-candidate, demotion-candidate, and eliminated model roles from live/shadow evidence. Manager may schedule the request and persist the receipt, but it must not independently choose the active production pointer.

Deferred decisions, rejected decisions, failed runs, partial evidence, stale configs, target-only substrate runs, or route-only artifacts cannot activate production pointers.

AUROC is ranking diagnostic evidence, not a standalone hard promotion gate. Promotion settlement must preserve AUROC/ROC, PR-AUC, calibration, and Brier evidence, but guardrails are based on sample sufficiency, point-in-time integrity, positive excess return, acceptable drawdown/tail behavior, high-score tail-risk separation, positive intended-threshold utility, and acceptable bad-fill / model-missed-winner rates.

High-score tail-risk settlement is deterministic and fixed-input. Evaluation must block promotion when high-score filled losses reach the minimum tail-loss count and filled winners versus filled losers have near-zero or inverted score separation. It must also block high-score tail-loss candidates whose filled-trade evidence is below the minimum tail-risk sample count. Short-DTE concentration is weak option-selection evidence only when it reaches the same minimum tail-loss count, and must be carried as a regression/follow-up unless confirmed by stronger option-selection evidence. Feature timing/leakage, liquidity/spread/fill realism, and regime/event miss remain evidence requirements until point-in-time feature traces, quote/fill evidence, or M06 event overlays are attached.

For the first accepted model bundle, evaluation may set `first_model_bootstrap = true`. That bundle's own frozen settlement run becomes the bootstrap baseline for later anonymous incumbent comparisons. This is a promotion/readiness exception only; it still cannot activate a production pointer without execution-owned shadow-cycle evidence.

## Failure Attribution Boundary

Failure attribution is a first-class task between replay and evaluation. It is not the same as evaluation and it is not limited to M06 event research. It investigates replay misses, residual alpha errors, bad target selection, omitted target combinations, overblocking, underblocking, position-management mistakes, option-expression drag, and event/co-event explanations.

Replay-derived failure triage is only the first bookkeeping step. A
`post_replay_failure_triage_receipt` may identify failed fills, missed winners,
and other candidate failure rows, but it does not satisfy M06
EventRiskGovernor attribution. M06 attribution requires a separate receipt
produced by the event-risk route with failure-scope triage, point-in-time event
observations or candidates, event-evidence refs, and control/co-event/confounder
analysis. Evaluation must not treat generic failure triage rows as completed
M06 event attribution.

The manager-owned historical workflow therefore has two explicit post-replay
steps before evaluation: first `post_replay_failure_triage`, then
`residual_event_governance`. If failure triage is ready but no reviewed
point-in-time event evidence exists, M06 must back off and prepare the
bounded event-feed backfill task keys needed to materialize event observations;
that preparation is not itself attribution and does not call providers.

The same boundary is required in live operation. Execution may run C07 as a
realtime failure/deviation watch during market hours, then run settlement
attribution after the regular session closes or in another explicitly accepted
off-hours window. Realtime watch may produce warning evidence for C03/C05/C06
review paths, but it must not mutate intraday entry, lifecycle, sizing, or
execution decisions by itself. If C07 identifies an event or anomaly that has not
been trained and accepted through M06/Layer 4, it may only emit a
provisional untrained-event risk estimate from model-failure severity and
supporting evidence. That estimate must be routed to the trading-review agent
before it can affect a live block, reduce, exit, or human-review path.
Evaluation may use attribution evidence, but evaluation must not silently invent
attribution labels inside promotion scoring.

M04/M05 boundary attribution is a manager-side diagnostic helper for this
failure-attribution lane. `scripts/tasks/build_model_group_layer_attribution.py`
reads an existing replay `decision_rows.jsonl` and writes compact cohort, score
bin, tail-loss, optional M05 unfilled-filter, gate-sweep, row-level
counterfactual, and parameter-level replay summaries. It also writes a
parameter replay-review report, a suspect-parameter counterfactual report, and a
focused high-score filled tail-loss packet that compares high-score losing fills
with matched high-score non-loss fills. For suspect parameters, it also writes a
fixed-input M04/M05 mechanism review with `m04_component_diagnostics.csv`,
`m05_selection_mechanics.csv`, `m04_variant_counterfactual.csv`,
`m05_dte_policy_sensitivity.csv`, `m05_hard_filter_overlap.csv`, and
`m04_m05_mechanism_review_report.json` so the repair question can distinguish
M04 component weighting/direction from M05 option-expression DTE sensitivity,
hard-filter overlap, or filled-subset selection mechanics. It separates weak
replay evidence into three explicit diagnostic classes:

- data insufficiency, such as too few filled option rows, sparse score bins, or
  missing point-in-time option candidates;
- execution/connection failure, such as M04/M05 producing an intended trade with
  an eligible or selected contract that replay did not fill;
- model-mechanism defect, such as high-score filled tail losses, non-monotonic
  filled score bins, or M05 scores that do not separate filled winners from
  filled losers.

It is fixed-input evidence only: it must not call providers, mutate SQL or
storage source data, change promotion decisions, relax option filters, retrain
models, activate models, or write active configs. Gate-sweep rows and
parameter-level bucket rows are diagnostic evidence, not threshold-selection
authority. Parameter-level replay review may classify a parameter as
directionally useful, weak/sample-limited, or suspect/requires redesign from
fixed replay correlation and bucket spreads, but it must not claim causality.
Suspect-parameter counterfactual rows may triage the next repair question into
filled-subset selection effect, parameter direction/definition inversion, or M04
component weight/direction follow-up, but they must not rewrite parameters or
select thresholds.
M04/M05 mechanism review rows may identify inverted M04 component behavior inside
the M04-open/M05-pass/filled subset or positive-label M04-open/M05-pass rows lost
to option-expression filters. The variant counterfactual and DTE sensitivity rows
may compare fixed-input M04 score-combination variants or DTE-filter pressure,
but they remain diagnostic-only and cannot change weights, option filters, or
promotion gates.
High-score tail-loss classification must not invent causes from missing
evidence: feature timing, liquidity/spread/fill realism, and regime/event miss remain
`unknown_requires_evidence` unless the fixed replay rows contain the needed
point-in-time evidence. The tool's role is to decide the next bounded
counterfactual or repair question when promotion fails due to overblocking,
underblocking, option-expression drag, alpha calibration, or drawdown.

## M06 / Layer 4 Rule

M06 event-risk research may propose a promotion packet. Layer 4 may consume only accepted event/strategy-failure factors. Event text, raw abnormal activity, unknown-overlap activity bridge evidence, and C07 provisional untrained-event risk estimates cannot be promoted directly.

## Useful Commands

```bash
PYTHONPATH=src /root/projects/trading-manager/.venv/bin/python scripts/tasks/plan_model_promotion_review.py --model option_expression_model --candidate-ref trading-model://promotion-candidates/mpcand_example
PYTHONPATH=src /root/projects/trading-manager/.venv/bin/python scripts/tasks/build_agent_model_promotion_decision.py --promotion-request-ref manager_request://model-promotion/example --decision-status defer --decision-reason "missing production calibration evidence"
PYTHONPATH=src /root/projects/trading-manager/.venv/bin/python scripts/tasks/build_model_group_layer_attribution.py --decision-rows /path/to/decision_rows.jsonl --output-dir /path/to/diagnostic_run --m05-unfilled-diagnostics /path/to/m05_unfilled_diagnostics.csv --counterfactual-gate-sweep /path/to/counterfactual_gate_sweep.csv --high-score-threshold 0.8
```
