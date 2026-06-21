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

Promotion acceptance is bundle-scoped. Model-local evidence remains available for diagnostics, regression attribution, and retraining priority, but it must not create independent promotion, shadow, live, or reusable-production acceptance for a single layer or partial substack unless an accepted lifecycle contract explicitly defines that component-local role.

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

Replay review is the first-class task between replay and M06. It is not the same as evaluation and it is not limited to event research. It investigates replay misses, residual alpha errors, bad target selection, omitted target combinations, overblocking, underblocking, position-management mistakes, option-expression drag, and the component-funnel layer where the replay first diverged. M06 runs after replay review and owns event/co-event explanations.

Replay review is path-conditioned. A miss is reviewable only inside the
information and upstream selection path the replay row actually observed. If an
upstream layer selected the wrong sector, later layers continue inside that
selected sector; if a target layer selected the wrong target, option-expression
review continues inside that selected target. Global hindsight winners may be
reported as separate oracle diagnostics, but they must not become
`missed_good`, model-missed-winner, or post-replay review rows for downstream
layers unless their candidate set was point-in-time feasible inside the current
selected path.

Replay review is hindsight grading over point-in-time available choices. It may
use future realized returns, drawdown, slippage, missed opportunity, and related
outcome windows to score each action that was actually available at decision
time. Future outcomes are review labels, not replay inputs: they must not expand
the candidate set, alter the point-in-time decision state, or create downstream
training/scoring features without preserving timestamp boundaries. The core
review question is which action later proved best within the `available_action`
set at timestamp `t`, how far the chosen action lagged that best available
action, and which component first caused the gap through filtering, ranking,
gating, sizing, timing, or execution.

Each `post_replay_review_row` therefore carries both the action comparison and
the first-gap attribution needed for operator review:

- `chosen_action` and `available_action` record the point-in-time action set.
- `chosen_action_return` and `best_available_action_return` record the
  hindsight outcome assigned to the chosen and best available actions.
- `best_available_action_by_future_outcome` and `regret_to_best_available`
  quantify regret inside the action set.
- `first_gap_component`, `first_gap_mechanism`, and `layer_attribution`
  identify the first component-funnel gap without expanding beyond the observed
  selected path.

The `post_replay_review_receipt` embeds
`post_replay_review_diagnostic_summary` so dashboard and operator surfaces can
scan total regret, top regret rows, best-action counts, and first-gap
component/mechanism counts before reruns or M06 attribution.

Replay review is only the first post-replay diagnostic step. A
`post_replay_review_receipt` may identify failed fills, missed winners,
and other candidate failure rows, but it does not satisfy M06
EventRiskGovernor attribution. M06 attribution requires a separate receipt
produced by the event-risk route with replay-review scope, point-in-time event
observations or candidates, event-evidence refs, and control/co-event/confounder
analysis. Evaluation must not treat generic replay review rows as completed
M06 event attribution.

Replay review must not complete when reviewable rows lack the future outcome or
return data needed to quantify hindsight grading. In that case it emits
`post_replay_review_data_requirement` rows under
`post_replay_review_requirements/.../replay_review_data_requirements.jsonl` and
backs off. Those requirement rows are acquisition or replay-repair inputs only;
they are not reviewed failures and they do not satisfy downstream attribution.

The manager-owned historical workflow therefore has two explicit post-replay
steps before evaluation: first `model_group.replay_review`, then M06 Event Risk
Governor attribution (`model_group.residual_event_governance`). If replay review is ready but no reviewed
point-in-time event evidence exists, M06 must back off and prepare the
bounded event-feed backfill task keys needed to materialize event observations;
that preparation is not itself attribution and does not call providers.

The same boundary is required in live operation. Execution may run C07 as a
realtime failure/deviation watch during market hours, then run settlement
attribution after the regular session closes or in another explicitly accepted
off-hours window. Realtime watch may produce warning evidence for C03/C05/C06
review paths, but it must not mutate intraday entry, lifecycle, sizing, or
execution decisions by itself. If C07 identifies an event or anomaly that has not
been trained and accepted through M06/M03 event-state, it may only emit a
provisional untrained-event risk estimate from model-failure severity and
supporting evidence. That estimate must be routed to the trading-review agent
before it can affect a live block, reduce, exit, or human-review path.
Evaluation may use attribution evidence, but evaluation must not silently invent
attribution labels inside promotion scoring.

M04/M05 boundary attribution is a manager-side diagnostic helper for this
failure-attribution lane. `scripts/tasks/build_model_group_layer_attribution.py`
reads an existing replay `decision_rows.jsonl` and writes compact cohort, score
bin, tail-loss, optional M05 unfilled-filter, gate-sweep, row-level
counterfactual, operation-component, review-projection, component-surface, and
parameter-level replay summaries. The canonical review entry is
`operation_component_review_packet.json` with companion
`operation_component_review_packet.csv`, `operation_component_flow.csv`, and
`operation_review_projection_matrix.csv`. These files use live/replay action
components as the first axis: C01 intake, C02 entry, C03 lifecycle, C04
expression review, C05 order intent, C06 execution gate, and C07 failure review.
Models and legacy decision surfaces are not treated as components. Instead,
`operation_review_projection_matrix.csv` maps the older diagnostic surfaces under
the operation that consumed or exposed them: background and target state under
C01, event and underlying-entry decision under C02, option selection and selected
contract path materialization under C04, fill/execution under C06, and residual
event or settled prediction quality under C07. C03 lifecycle is marked
`not_applicable_for_candidate_entry_replay` for candidate-entry replay rows that
do not manage an existing position.

The older `decision_surface_component_matrix.csv`,
`component_model_mapping.csv`, `component_survival_quality_flow.csv`, and
`component_review_packet.json` remain diagnostic projection evidence for
model-ref coverage and historical C01-C09 surface ordering. They are not the
canonical operation-component axis. Model-asset rollups are secondary and must
not include rows that were excluded from settled prediction-quality metrics by
missing path, expression, execution, or settlement evidence. Missing selected
option paths are expression materialization censoring, not model wins or losses;
only settled-eligible rows contribute outcome quality metrics. Every operation
component row separates point-in-time evidence from retrospective outcome labels,
lists the internal review refs that compose the component, marks missing review
outputs, and records whether an operation fault can be assigned or must remain an
attribution gap. A component with missing diagnostics is not treated as neutral
just because the final loss is first visible downstream. The packet expects
replay `decision_rows.jsonl` to carry `model_layer_refs` and
`model_layer_diagnostics` for model surfaces when they participate; selected-path
materialization, execution/fill, and settled quality remain non-model or
downstream review projections. The helper also writes a parameter replay-review report, a
suspect-parameter counterfactual report, and a focused
high-score filled tail-loss packet that compares high-score losing fills with
matched high-score non-loss fills. For suspect parameters, it also writes a
fixed-input M04/M05 mechanism review with `m04_component_diagnostics.csv`,
`m05_selection_mechanics.csv`, `m04_variant_counterfactual.csv`,
`portfolio_capacity_counterfactual.csv`,
`portfolio_capacity_counterfactual_report.json`, `m05_dte_policy_sensitivity.csv`,
`m05_hard_filter_overlap.csv`, and `m04_m05_mechanism_review_report.json` so
the repair question can distinguish M04 component weighting/direction from M05
option-expression DTE sensitivity, hard-filter overlap, filled-subset selection
mechanics, or C07 capacity concentration. It separates weak
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
Portfolio capacity counterfactual rows may compare fixed-input replay-selected,
top-N-by-replay-rank, and budget-fraction variants to show whether C07 capacity
would have amplified prior damage or pulled it back. They are a review surface
only, not portfolio policy selection, threshold tuning, or promotion authority.
High-score tail-loss classification must not invent causes from missing
evidence: feature timing, liquidity/spread/fill realism, and regime/event miss remain
`unknown_requires_evidence` unless the fixed replay rows contain the needed
point-in-time evidence. The tool's role is to decide the next bounded
counterfactual or repair question when promotion fails due to overblocking,
underblocking, option-expression drag, alpha calibration, or drawdown.

## M06 / M03 event-state Rule

M06 event-risk research may propose a promotion packet. M03 event-state may consume only accepted event/strategy-failure factors. Event text, raw abnormal activity, unknown-overlap activity bridge evidence, and C07 provisional untrained-event risk estimates cannot be promoted directly.

## Useful Commands

```bash
PYTHONPATH=src /root/projects/trading-manager/.venv/bin/python scripts/tasks/plan_model_promotion_review.py --model option_expression_model --candidate-ref trading-model://promotion-candidates/mpcand_example
PYTHONPATH=src /root/projects/trading-manager/.venv/bin/python scripts/tasks/build_agent_model_promotion_decision.py --promotion-request-ref manager_request://model-promotion/example --decision-status defer --decision-reason "missing production calibration evidence"
PYTHONPATH=src /root/projects/trading-manager/.venv/bin/python scripts/tasks/build_model_group_layer_attribution.py --decision-rows /path/to/decision_rows.jsonl --output-dir /path/to/diagnostic_run --m05-unfilled-diagnostics /path/to/m05_unfilled_diagnostics.csv --counterfactual-gate-sweep /path/to/counterfactual_gate_sweep.csv --high-score-threshold 0.8
```
