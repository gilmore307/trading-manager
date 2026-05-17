# Model Promotion

Promotion is the reviewed transition from model evidence to production-eligible configuration. It is not automatic scheduler progress.

## Required Evidence

A promotion packet should identify:

- model/layer/candidate refs;
- dataset snapshot and split refs;
- labels and evaluation refs;
- baseline comparisons;
- leakage checks;
- stability and sample-size evidence;
- known failure modes;
- downstream activation scope;
- reviewer/agent decision evidence.

## Activation Rule

Production activation requires an accepted `agent_model_promotion_decision` with explicit activation scope. Advisory reviews, missing reviews, deferred decisions, rejected decisions, failed runs, partial evidence, stale configs, or route-only artifacts cannot activate production pointers.

## Layer 9 / Layer 4 Rule

Layer 9 event-risk research may propose a promotion packet. Layer 4 may consume only accepted event/strategy-failure factors. Event text, raw abnormal activity, and unknown-overlap activity bridge evidence cannot be promoted directly.

## Useful Commands

```bash
PYTHONPATH=src python3 scripts/tasks/plan_model_promotion_review.py --model model_08_option_expression --candidate-ref trading-model://promotion-candidates/mpcand_example
PYTHONPATH=src python3 scripts/tasks/build_agent_model_promotion_decision.py --review-target-ref storage://trading-model/promotion-candidates/mpcand_example.json --decision-status defer --decision-reason "missing production calibration evidence"
```
