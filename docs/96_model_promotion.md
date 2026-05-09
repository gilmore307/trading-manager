# Model Promotion

`trading-manager` owns one promotion review entrypoint for every model layer.

The model repositories produce evidence. The manager records and reviews that evidence through one control-plane path.

```text
model-specific evidence producer
  -> model_promotion_review_v1 manager request
  -> review_decision_v1
  -> activation_record_v1 only if approved
```

Do not create one promotion system per model. Layer-specific semantics belong in evidence adapters, metric names, labels, baseline ladders, and gate policy refs. The request/review/decision/activation skeleton is shared.

## Unified Request

Use `model_promotion_review_v1` for all model layers.

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

Add `--write` only after the request payload has been reviewed. `--write` persists the request rows to `trading_manager.manager_request`; it does not approve promotion and does not activate configs.

Build a generic review decision artifact:

```bash
PYTHONPATH=src python3 scripts/tasks/build_review_decision.py \
  --review-target-ref storage://trading-model/promotion-candidates/mpcand_example.json \
  --decision-status defer \
  --decision-reason "missing production calibration evidence" \
  --condition supply_real_sample_eval
```

`review_decision_v1` is an artifact-level decision record. Only `decision_status=approve` can be used to build an `activation_record_v1`; deferred, rejected, failed, partial, revoked, or superseded decisions cannot activate configs.

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
- reviewed decision records;
- activation records;
- cross-layer dependency gates;
- the rule that deferred or rejected decisions cannot activate configs.

`trading-storage` owns bulky evidence payloads and retained review artifacts.

## Registered Models

| Layer | Model id | Model | Output contract |
|---|---|---|---|
| 1 | `model_01_market_regime` | `MarketRegimeModel` | `market_context_state` |
| 2 | `model_02_sector_context` | `SectorContextModel` | `sector_context_state` |
| 3 | `model_03_target_state_vector` | `TargetStateVectorModel` | `target_context_state` |
| 4 | `model_04_event_overlay` | `EventOverlayModel` | `event_context_vector` |
| 5 | `model_05_alpha_confidence` | `AlphaConfidenceModel` | `alpha_confidence_vector` |
| 6 | `model_06_position_projection` | `PositionProjectionModel` | `position_projection_vector` |
| 7 | `model_07_underlying_action` | `UnderlyingActionModel` | `underlying_action_plan` |
| 8 | `model_08_option_expression` | `OptionExpressionModel` | `option_expression_plan` |

## Guardrails

- A promotion request is not a promotion approval.
- Evidence generation does not imply activation.
- Activation requires an approving `review_decision_v1`.
- Deferred, rejected, failed, or partial reviews must not move production pointers.
- Model-specific fields stay in model evidence; manager only stores refs and generic review facts.
