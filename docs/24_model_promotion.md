# Model Promotion Scheduling

Manager owns scheduling and request preparation for model promotion/evaluation work. Benchmark judgment, promotion eligibility, and promotion readiness belong to `trading-evaluation`; runtime active/shadow model selection belongs to `trading-execution`.

When a reviewer agent is used for promotion judgment, the request must require the workspace skill `skills/openclaw/promotion-evaluation-review`. The agent review is advisory evidence only; `trading-evaluation` deterministic checks own eligibility and readiness records.

## Required Evidence

A promotion packet should identify:

- model/layer/candidate refs;
- dataset snapshot and split refs;
- labels and evaluation refs;
- baseline comparisons;
- leakage checks;
- stability and sample-size evidence;
- known failure modes;
- downstream shadow/activation scope;
- evaluation decision evidence.

## Activation Boundary

Manager must not activate production pointers. Offline promotion requires `trading-evaluation` evidence: accepted benchmark settlement, `promotion_eligibility_decision`, `promotion_readiness_record`, and rollback/config refs. Runtime activation requires `trading-execution` shadow-cycle evidence: active model live performance, promoted-but-not-active shadow performance, realtime candidate roster, and elimination rationale where applicable. Deferred decisions, rejected decisions, failed runs, partial evidence, stale configs, or route-only artifacts cannot activate production pointers.

## Layer 9 / Layer 4 Rule

Layer 9 event-risk research may propose a promotion packet. Layer 4 may consume only accepted event/strategy-failure factors. Event text, raw abnormal activity, and unknown-overlap activity bridge evidence cannot be promoted directly.

## Useful Commands

```bash
PYTHONPATH=src python3 scripts/tasks/plan_model_promotion_review.py --model option_expression_model --candidate-ref trading-model://promotion-candidates/mpcand_example
PYTHONPATH=src python3 scripts/tasks/build_agent_model_promotion_decision.py --promotion-request-ref manager_request://model-promotion/example --decision-status defer --decision-reason "missing production calibration evidence"
```
