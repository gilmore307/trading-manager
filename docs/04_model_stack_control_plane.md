# Model Stack Control Plane

## Purpose

This file gives `trading-manager` a concise manager-side view of the accepted Layer 1-8 model stack.

It is not the model design authority. Detailed model semantics, features, labels, evaluation code, and local deterministic scaffolds belong in `trading-model` and `trading-data`. This file owns only the control-plane interpretation that `trading-manager` needs for request planning, registry naming, promotion review, and boundary enforcement.

## Manager-Side Stack Summary

| Layer | Model surface | Primary concept | Manager-facing output/handoff | Boundary reminder |
|---|---|---|---|---|
| 1 | `model_01_market_regime` | Market context | `market_context_state` | Conditions downstream layers; does not rank sectors, targets, strategies, positions, options, or actions. |
| 2 | `model_02_sector_context` | Sector/industry context | `sector_context_state` | Conditions anonymous target candidates; does not select final symbols or actions. |
| 3 | `model_03_target_state_vector` | Anonymous target context | `target_context_state` | Produces target-state evidence; does not emit alpha confidence, position size, option expression, or final action. |
| 4 | `model_04_event_overlay` | Event overlay context | `event_context_vector` | Adds event evidence/risk, including `price_action` events; does not execute or approve trades. |
| 5 | `model_05_alpha_confidence` | Calibrated alpha confidence | `alpha_confidence_vector` | Estimates adjusted alpha/EV/risk; does not choose target exposure, action, option contract, or order. |
| 6 | `model_06_position_projection` | Target holding-state projection | `position_projection_vector` | Projects abstract exposure/gap/utility; does not emit buy/sell/hold orders or mutate broker/account state. |
| 7 | `model_07_underlying_action` | Offline direct-underlying action thesis | `underlying_action_plan` plus `underlying_action_vector` | Plans direct stock/ETF thesis fields; not broker order construction or routing. |
| 8 | `model_08_option_expression` | Offline option-expression thesis | `option_expression_plan` plus `expression_vector` | Chooses expression/contract constraints for review; not order placement, fills, or account mutation. |

## Source/Feature Numbering Is Not Always Model-Layer Numbering

Model surfaces use `model_NN_*` where `NN` is the model layer.

Data source and feature surfaces may keep source-family numbering that reflects the accepted data-production contract rather than the model layer number. Current important examples:

- `source_04_event_overlay` feeds Layer 4 event overlay evidence.
- `source_05_option_expression` feeds Layer 8 option-expression inputs; it is not Layer 5 AlphaConfidenceModel.
- `feature_08_option_expression` is the deterministic Layer 8 model-facing feature surface produced from accepted option-expression inputs.
- `source_06_position_execution` is selected-contract/position-execution context for Layer 8 option-expression review; it is not Layer 6 PositionProjectionModel.

When a source/feature/model name crosses repository boundaries, the canonical shared name must be registered through `scripts/registry/` before implementation depends on it.

## Control-Plane Responsibilities

`trading-manager` may:

- plan manager requests for data/model/storage/execution/dashboard review paths;
- validate request payload shape and live-call approvals;
- maintain registry names, kind boundaries, and naming rules;
- record promotion-review requests, review-decision artifacts, and activation-record artifacts;
- enforce that deferred/rejected/failed/partial reviews cannot activate configs.

`trading-manager` must not:

- fetch provider data;
- run feature generation, model training, or model inference as production behavior;
- activate a model without an approving `review_decision_v1`;
- dispatch live provider calls without `live_call_approval_v1`;
- construct/place broker orders, process fills, mutate positions, or mutate account state.

## Registry and Promotion Relationship

Registry rows make shared names visible and reviewable. They do not make a model production-active.

Promotion remains governed by `docs/96_model_promotion.md`: model repositories produce evidence, `trading-manager` records/reviews promotion requests and decisions, and activation requires an approved review decision plus an activation record. Closeout documentation does not override those gates.
