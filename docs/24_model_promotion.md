# Model Promotion Scheduling

Manager owns scheduling and request preparation for model promotion/evaluation work. Benchmark judgment, promotion eligibility, active model config release, and model activation records belong to `trading-evaluation`.

When a reviewer agent is used for promotion judgment, the request must require the workspace skill `skills/openclaw/promotion-evaluation-review`. The agent review is advisory evidence only; `trading-evaluation` deterministic checks own eligibility and activation records.

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
- evaluation decision evidence.

## Activation Boundary

Manager must not activate production pointers. Activation requires `trading-evaluation` evidence: accepted benchmark settlement, `promotion_eligibility_decision`, active model config ref, model activation record, and rollback ref. Deferred decisions, rejected decisions, failed runs, partial evidence, stale configs, or route-only artifacts cannot activate production pointers.

## Layer 9 / Layer 4 Rule

Layer 9 event-risk research may propose a promotion packet. Layer 4 may consume only accepted event/strategy-failure factors. Event text, raw abnormal activity, and unknown-overlap activity bridge evidence cannot be promoted directly.

## Useful Commands

```bash
PYTHONPATH=src python3 scripts/tasks/plan_model_promotion_review.py --model option_expression_model --candidate-ref trading-model://promotion-candidates/mpcand_example
PYTHONPATH=src python3 scripts/tasks/build_agent_model_promotion_decision.py --promotion-request-ref manager_request://model-promotion/example --decision-status defer --decision-reason "missing production calibration evidence"
```
