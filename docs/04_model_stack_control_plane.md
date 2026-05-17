# Model Stack Control Plane

## Purpose

This file gives `trading-manager` a concise manager-side view of the accepted Layer 1-9 model stack.

It is not the model design authority. Detailed model semantics, features, labels, evaluation code, and local deterministic scaffolds belong in `trading-model` and `trading-data`. This file owns only the control-plane interpretation that `trading-manager` needs for request planning, registry naming, promotion review, and boundary enforcement.

This file also records the completed transition: the conceptual order changed on 2026-05-17 and active physical script/package/table names now use the nine-layer numbering. Historical/applied migration records may retain earlier names for auditability.

## Manager-Side Stack Summary

| Conceptual layer | Model boundary | Current physical surface | Primary concept | Manager-facing output/handoff | Boundary reminder |
|---|---|---|---|---|---|
| 1 | `MarketRegimeModel` | `model_01_market_regime` | Market context | `market_context_state` | Conditions downstream layers; does not rank sectors, targets, strategies, positions, options, or actions. |
| 2 | `SectorContextModel` | `model_02_sector_context` | Sector/industry context | `sector_context_state` | Conditions anonymous target candidates; does not select final symbols or actions. |
| 3 | `TargetStateVectorModel` | `model_03_target_state_vector` | Anonymous target context | `target_context_state` | Produces target-state evidence; does not emit alpha confidence, position size, option expression, or final action. |
| 4 | `EventFailureRiskModel` | current `model_04_event_failure_risk` | Reviewed event/strategy-failure risk | `event_failure_risk_vector` | Consumes only agent-accepted event/strategy-failure evidence; may recommend alpha/entry/cap/disable conditioning, but not buy/sell/hold, sizing, expression choice, broker mutation, or destructive SQL/storage action. |
| 5 | `AlphaConfidenceModel` | current `model_05_alpha_confidence` | Calibrated alpha confidence | `alpha_confidence_vector` | Estimates adjusted alpha/EV/risk after accepted event-failure conditioning; does not choose target exposure, action, option contract, or order. |
| 6 | `PositionProjectionModel` | current `model_06_position_projection` | Target holding-state projection | `position_projection_vector` | Projects abstract exposure/gap/utility; does not emit buy/sell/hold orders or mutate broker/account state. |
| 7 | `UnderlyingActionModel` | current `model_07_underlying_action` | Offline direct-underlying action thesis | `underlying_action_plan` plus `underlying_action_vector` | Plans direct stock/ETF thesis fields; not broker order construction or routing. |
| 8 | `TradingGuidanceModel / OptionExpressionModel` | current `model_08_option_expression` | Offline trading guidance / option-expression thesis | `trading_guidance_record`, `option_expression_plan`, and expression/underlying plan refs | Produces the base offline guidance candidate for review; not order placement, fills, or account mutation. |
| 9 | `EventRiskGovernor / EventIntelligenceOverlay` | current `model_09_event_risk_governor` plus `source_09_event_risk_governor` | Residual event intelligence / risk overlay | `event_risk_intervention`, observation-pool evidence, and promotion-review packets | Reviews residual anomalies after the base stack; may warn/block/cap/review or propose Layer 4 promotion packets, but cannot auto-promote families or mutate broker/account state. |

## Source/Feature Numbering Is Not Always Model-Layer Numbering

Model semantics use the layer order above. Current physical model surfaces use the nine-layer numbering. Data source and feature surfaces may still use source-family numbering that reflects the accepted data-production contract rather than the model layer number. Current important examples:

- `source_09_event_risk_governor` feeds the Layer 9 event-risk-governor evidence path.
- `source_05_option_expression` feeds Layer 8 trading-guidance / option-expression inputs; it is not Layer 5 AlphaConfidenceModel.
- `feature_08_option_expression` is the current deterministic Layer 8 option-expression feature surface produced from accepted option-expression inputs.
- `source_06_position_execution` is selected-contract/position-execution context for option-expression review; it is not Layer 6 PositionProjectionModel.

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

## Event-Activity Bridge Control-Plane Rule

`event_activity_bridge` is the accepted contract for connecting event evidence to price, flow, liquidity, option, and prediction-market activity. It is especially useful when raw news is too hard to standardize semantically but observable activity gives a stable point-in-time lead/lag or confirmation/divergence structure.

Accepted relation types:

```text
pre_event_precursor
co_event_reaction
post_event_absorption
event_activity_divergence
unresolved_latent_hazard
```

Accepted explanation statuses:

```text
explained_by_known_event
partially_explained
unexplained
later_explained
review_required
```

Manager must preserve both sides of the bridge: event refs and activity refs. It must not let a later explanation rewrite the original point-in-time record; later explanations create follow-up bridge evidence for training/evaluation.

Before this bridge can become a separate model layer, manager must require an activity-price proof gate. The gate must show forward price/path relationship, incremental residual value after existing model controls, cross-market confirmation value, and out-of-sample stability. Current-move description alone is not sufficient.

Manager must also require event-family scouting before broad event-risk training. Raw option abnormality plus raw news proximity is not a sufficient promotion unit. A reviewed `event_family_scouting_packet_v1` must define family inclusion/exclusion rules, lifecycle clocks, materiality/surprise rules, source precedence, abnormal-activity bridge rules, controls, forward labels, coverage gates, and early-stop criteria. Current accepted statuses: standalone option abnormality, threshold-only option refinement, and raw-news-proximate option abnormality are `deferred_low_signal`; earnings/guidance is only `scouting` under `trading-model/docs/101_earnings_guidance_event_family_packet.md`.

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

## Cross-Section Activity-Price Study Governance

The manager control plane must treat the activity-price proof gate as a reviewed cross-sectional study, not a single-symbol anecdote. Pilot symbols such as RCAT may debug data joins and event/activity windows, but promotion requires size, sector/theme, and event-family coverage.

The accepted study must record cohort definition, controls, forward labels, horizon set, split policy, failure modes, and whether evidence is sufficient to open an `EventActivityBridgeModel` promotion task.

## Option-Activity Direction Study Governance

Manager must treat option-direction evidence as a second-gate study after direction-neutral path expansion. A call-buying surge may be bullish only when side/aggressor/opening evidence supports that interpretation. Raw call or put volume alone is insufficient for directional promotion.

Reviewed option-direction study tasks must preserve the underlying contract, right, side/aggressor evidence, sweep/block context, opening/open-interest context, IV/skew context, and signed directional forward labels for both underlying and option contract where available.
