# Model Promotion

`trading-manager` owns one promotion review entrypoint for every model layer.

The model repositories produce evidence. The manager records and reviews that evidence through one control-plane path, then calls an agent decision step. The agent approves, defers, or rejects from evidence; this is not a routine owner approval prompt.

```text
model-specific evidence producer
  -> model_promotion_review manager request
  -> agent_model_promotion_decision
  -> activation_record only if agent-approved
```

Do not create one promotion system per model. Layer-specific semantics belong in evidence adapters, metric names, labels, baseline ladders, and gate policy refs. The request/evidence/agent-decision/activation skeleton is shared.

## Unified Request

Use `model_promotion_review` for all model layers.

The request targets the manager review helper:

```text
target_repo_id = trading-manager
target_component_id = manager_model_promotion_review
target_component_kind = review_helper
```

The request carries concise control-plane facts:

- model id and model layer;
- candidate ref;
- evaluation run refs;
- evidence refs;
- priority and deadline;
- policy refs;
- parameter ref for the full request payload.

The full review payload belongs behind `parameter_ref`, not inside manager SQL.

## Scripts

Plan review requests without mutating SQL:

```bash
PYTHONPATH=src python3 scripts/tasks/plan_model_promotion_review.py \
  --model model_08_option_expression \
  --candidate-ref trading-model://promotion-candidates/mpcand_example \
  --evaluation-run-ref trading-model://eval-runs/mdevrun_example \
  --evidence-ref storage://trading-model/evidence/example.json
```

Plan one request for every registered model layer:

```bash
PYTHONPATH=src python3 scripts/tasks/plan_model_promotion_review.py \
  --all \
  --candidate-ref trading-model://promotion-candidates/mpcand_example
```

Add `--write` only after the request payload is ready for agent-managed automation. `--write` persists the request rows to `trading_manager.manager_request`; it does not approve promotion and does not activate configs.

Build a generic decision artifact only through the script-called agent promotion-decision path. Until that agent decision surface exists, legacy `review_decision` builders are evidence/advisory scaffolding only and must not activate configs:

```bash
PYTHONPATH=src python3 scripts/tasks/build_review_decision.py \
  --review-target-ref storage://trading-model/promotion-candidates/mpcand_example.json \
  --decision-status defer \
  --decision-reason "missing production calibration evidence" \
  --condition supply_real_sample_eval
```

The accepted production boundary is `agent_model_promotion_decision`. Only an agent decision with approved activation scope may be used to build an `activation_record`; deferred, rejected, failed, partial, revoked, superseded, or legacy advisory review decisions cannot activate configs.

## Boundary

`trading-model` owns:

- model output generation;
- labels;
- evaluation computation;
- metric computation;
- model-specific evidence packages.

`trading-manager` owns:

- the generic promotion review request;
- review policy and checklist;
- script-called agent decision records;
- activation records;
- cross-layer dependency gates;
- the rule that deferred or rejected decisions cannot activate configs.

`trading-storage` owns bulky evidence payloads and retained review artifacts.

## Promotion and storage lifecycle boundary

Promotion scripts and review helpers may classify artifact retention intent, but they must not run file cleanup, compression, archive, SQL detach/drop, or deletion executors.

Accepted boundary:

```text
promotion classifies artifacts
manager schedules lifecycle
storage executes lifecycle
```

Promotion outputs should mark promoted model bodies and required lineage as permanently retained, and may emit retention hints for regenerable intermediates. Any storage lifecycle work created by promotion must enter the manager task system as `storage_lifecycle_request`, where it can be prioritized, scheduled, summarized, and evaluated against lifecycle policy. `agent_storage_lifecycle_decision` records the policy/agent decision without mutating storage; when the request fits accepted rules and protected-set checks pass, it is not a human approval prompt. `trading-storage` remains the owner of protected-set checks, physical compression/archive/restore/delete actions, receipts, and tombstones.

## Registered Models

This table is the manager-side promotion target map. It records review targets and expected output/handoff contracts; it does not activate any model.

| Layer | Model id | Model | Primary output contract | Secondary/vector review surface |
|---|---|---|---|---|
| 1 | `model_01_market_regime` | `MarketRegimeModel` | `market_context_state` | registered `1_*` market-context score tokens |
| 2 | `model_02_sector_context` | `SectorContextModel` | `sector_context_state` | registered `2_*` sector-context score tokens |
| 3 | `model_03_target_state_vector` | `TargetStateVectorModel` | `target_context_state` | registered `3_*` target-state score-family tokens |
| 4 | `model_04_alpha_confidence` | `AlphaConfidenceModel` | `alpha_confidence_vector` | legacy physical `model_05_alpha_confidence` evidence and `5_*` score tokens until migration |
| 5 | `model_05_position_projection` | `PositionProjectionModel` | `position_projection_vector` | legacy physical `model_06_position_projection` evidence and `6_*` score tokens until migration |
| 6 | `model_06_underlying_action` | `UnderlyingActionModel` | `underlying_action_plan` | legacy physical `model_07_underlying_action` evidence and `7_*` score tokens until migration |
| 7 | `model_07_option_expression` | `OptionExpressionModel` under `TradingGuidanceModel` | `option_expression_plan` | legacy physical `model_08_option_expression` evidence and `8_*` score tokens until migration |
| 8 | `model_08_event_risk_governor` | `EventRiskGovernor` | `event_context_vector` / `event_risk_intervention` | registered event-context score-family tokens |

## Guardrails

- A promotion request is not a promotion decision.
- Evidence generation does not imply activation.
- Activation requires an approving `agent_model_promotion_decision`.
- Deferred, rejected, failed, partial, legacy advisory, or missing agent decisions must not move production pointers.
- Model-specific fields stay in model evidence; manager only stores refs and generic review facts.
