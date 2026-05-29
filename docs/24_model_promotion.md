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

AUROC is ranking diagnostic evidence, not a standalone hard promotion gate. Promotion settlement must preserve AUROC/ROC, PR-AUC, calibration, and Brier evidence, but guardrails are based on sample sufficiency, point-in-time integrity, positive excess return, acceptable drawdown/tail behavior, positive intended-threshold utility, and acceptable bad-fill / model-missed-winner rates.

For the first accepted model bundle, evaluation may set `first_model_bootstrap = true`. That bundle's own frozen settlement run becomes the bootstrap baseline for later anonymous incumbent comparisons. This is a promotion/readiness exception only; it still cannot activate a production pointer without execution-owned shadow-cycle evidence.

## Failure Attribution Boundary

Failure attribution is a first-class task between replay and evaluation. It is not the same as evaluation and it is not limited to Layer 10 event research. It investigates replay misses, residual alpha errors, bad target selection, omitted target combinations, overblocking, underblocking, position-management mistakes, option-expression drag, and event/co-event explanations.

The same boundary is required in live operation. Execution may run C07 as a
realtime failure/deviation watch during market hours, then run settlement
attribution after the regular session closes or in another explicitly accepted
off-hours window. Realtime watch may produce warning evidence for C03/C05/C06
review paths, but it must not mutate intraday entry, lifecycle, sizing, or
execution decisions by itself. If C07 identifies an event or anomaly that has not
been trained and accepted through Layer 10/Layer 4, it may only emit a
provisional untrained-event risk estimate from model-failure severity and
supporting evidence. That estimate must be routed to the trading-review agent
before it can affect a live block, reduce, exit, or human-review path.
Evaluation may use attribution evidence, but evaluation must not silently invent
attribution labels inside promotion scoring.

## Layer 10 / Layer 4 Rule

Layer 10 event-risk research may propose a promotion packet. Layer 4 may consume only accepted event/strategy-failure factors. Event text, raw abnormal activity, unknown-overlap activity bridge evidence, and C07 provisional untrained-event risk estimates cannot be promoted directly.

## Useful Commands

```bash
PYTHONPATH=src python3 scripts/tasks/plan_model_promotion_review.py --model option_expression_model --candidate-ref trading-model://promotion-candidates/mpcand_example
PYTHONPATH=src python3 scripts/tasks/build_agent_model_promotion_decision.py --promotion-request-ref manager_request://model-promotion/example --decision-status defer --decision-reason "missing production calibration evidence"
```
