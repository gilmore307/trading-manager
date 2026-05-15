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
| 4 | `model_04_alpha_confidence` | Calibrated alpha confidence | `alpha_confidence_vector` | Estimates adjusted alpha/EV/risk; does not choose target exposure, action, option contract, or order. Legacy physical code may still use `model_05_alpha_confidence` until migration. |
| 5 | `model_05_position_projection` | Target holding-state projection | `position_projection_vector` | Projects abstract exposure/gap/utility; does not emit buy/sell/hold orders or mutate broker/account state. Legacy physical code may still use `model_06_position_projection` until migration. |
| 6 | `model_06_underlying_action` | Offline direct-underlying action thesis | `underlying_action_plan` plus `underlying_action_vector` | Plans direct stock/ETF thesis fields; not broker order construction or routing. Legacy physical code may still use `model_07_underlying_action` until migration. |
| 7 | `model_07_trading_guidance` | Offline trading guidance / option-expression thesis | `trading_guidance_record` plus expression/underlying plan refs | Produces the base offline guidance candidate for review; not order placement, fills, or account mutation. Legacy physical code may still use `model_08_option_expression` until migration. |
| 8 | `event_risk_governor` | Event intelligence / risk overlay | `event_risk_intervention` plus event-adjusted risk guidance | Reviews the Layer 7 base guidance candidate for high-risk point-in-time events; may block/cap/reduce/nominate flatten/halt/review, but cannot mutate broker/account state. |

## Source/Feature Numbering Is Not Always Model-Layer Numbering

Model surfaces use `model_NN_*` where `NN` is the model layer.

Data source and feature surfaces may keep source-family numbering that reflects the accepted data-production contract rather than the model layer number. Current important examples:

- `source_04_event_overlay` feeds the conceptual Layer 8 event-risk-governor evidence path, despite its legacy physical number.
- `source_05_option_expression` feeds conceptual Layer 7 trading-guidance / option-expression inputs; it is not Layer 5 PositionProjectionModel.
- `feature_08_option_expression` is the deterministic option-expression feature surface produced from accepted option-expression inputs; its physical number remains legacy until migration.
- `source_06_position_execution` is selected-contract/position-execution context for option-expression review; it is not conceptual Layer 6 UnderlyingActionModel.

When a source/feature/model name crosses repository boundaries, the canonical shared name must be registered through `scripts/registry/` before implementation depends on it.

## Event Lifecycle Control-Plane Rule

Event-risk-governor requests and review artifacts must preserve event lifecycle timing. Manager-side planning must not treat a scheduled-known catalyst the same as an unscheduled surprise headline.

Accepted event lifecycle classes:

```text
scheduled_known_outcome_later
unscheduled_surprise
scheduled_recurring_data_release
multi_stage_developing_event
unknown
```

Required lifecycle clocks, when known or source-provided:

```text
event_awareness_time
event_scheduled_time
source_published_time
available_time
interpretation_time
resolution_time
reaction_window
```

Manager implications:

- A scheduled earnings or macro-calendar shell can create pre-event risk/planning records before the result is known.
- Result values, beat/miss, guidance, revisions, and realized reaction are invalid before the release artifact is visible by `available_time`.
- A surprise-news request cannot include a pre-event specific-event record; only background hazard/vulnerability evidence may predate the first credible source.
- Multi-stage events should add immutable stage/update refs rather than overwrite the original event row.

## Control-Plane Responsibilities

`trading-manager` may:

- plan manager requests for data/model/storage/execution/dashboard review paths;
- validate request payload shape and autonomous provider dispatchs;
- maintain registry names, kind boundaries, and naming rules;
- record promotion-review requests, script-called agent decision artifacts, and activation-record artifacts;
- enforce that deferred/rejected/failed/partial/missing agent decisions cannot activate configs.

`trading-manager` must not:

- fetch provider data;
- run feature generation, model training, or model inference as production behavior;
- activate a model without an approving `agent_model_promotion_decision`;
- dispatch broker/order/account mutations or model activation through the historical provider path;
- construct/place broker orders, process fills, mutate positions, or mutate account state.

## Registry and Promotion Relationship

Registry rows make shared names visible and reviewable. They do not make a model production-active.

Promotion remains governed by `docs/96_model_promotion.md`: model repositories produce evidence, `trading-manager` records promotion requests and script-called agent decisions, and activation requires an approved agent decision plus an activation record. Closeout documentation does not override those gates.
