# Architecture

This file is the manager-side map of the current Layer 1-9 stack. It is a routing and boundary guide, not the model-design authority.

## Module Map

| Docs band | Implementation surface | Purpose |
|---|---|---|
| `10_*` | `src/trading_registry/`, `scripts/registry/`, template surfaces | Registry and template authority. |
| `20_*` | `src/trading_manager_tasks/`, `scripts/tasks/`, scheduler/service definitions | Manager task system, historical planning, promotion, scheduler, and control-plane acceptance. |
| `30_*` | `src/trading_bigquery/`, `src/trading_web_search/`, shared helper policy | Shared helper package boundary. |

## Stack Map

| Layer | Boundary | Physical token family | Main concept | Manager-facing handoff | Hard boundary |
|---|---|---|---|---|---|
| 1 | `MarketRegimeModel` | `layer_01_market_regime`, `model_01_market_regime` | Broad-market context | `market_context_state` | No sector/target/action choice. |
| 2 | `SectorContextModel` | `layer_02_sector_context`, `model_02_sector_context` | Sector/industry context | `sector_context_state` | No final symbol/action choice. |
| 3 | `TargetStateVectorModel` | `layer_03_target_state_vector`, `model_03_target_state_vector` | Anonymous target context | `target_context_state` | No alpha, exposure, option, or action. |
| 4 | `EventFailureRiskModel` | `layer_04_event_failure_risk`, `model_04_event_failure_risk` | Reviewed event/strategy-failure conditioning | `event_failure_risk_vector` | Consumes only accepted evidence packets; no action or execution. |
| 5 | `AlphaConfidenceModel` | `layer_05_alpha_confidence`, `model_05_alpha_confidence` | Calibrated alpha confidence | `alpha_confidence_vector` | No exposure, option contract, or order. |
| 6 | `PositionProjectionModel` | `layer_06_position_projection`, `model_06_position_projection` | Abstract holding-state projection | `position_projection_vector` | No buy/sell/hold order. |
| 7 | `UnderlyingActionModel` | `layer_07_underlying_action`, `model_07_underlying_action` | Offline underlying thesis | `underlying_action_plan` | Not broker routing or order construction. |
| 8 | `EventRiskGovernor / EventIntelligenceOverlay` | `layer_08_event_risk_governor`, `model_08_event_risk_governor` | Residual event-risk review before final guidance | `event_risk_intervention`, review/provenance/promotion packets | May warn/block/cap/review; cannot auto-promote or trade. |
| 9 | `TradingGuidanceModel / OptionExpressionModel` | `layer_09_option_expression`, `model_09_option_expression` | Offline guidance and option-expression plan | `trading_guidance_record`, `option_expression_plan` | Not execution and not broker/account mutation. |

## Physical Surface Rule

Active code, scripts, registry rows, and docs should use the current layer numbers above. SQL migration history is append-only audit material and is not rewritten by documentation cleanup.

## Event Path Rule

Layer 8 may inspect event evidence and residual abnormal activity before final guidance. Layer 4 may consume only Layer 8 evidence packets that passed point-in-time checks, non-overlap checks, matched-control review, leakage review, and agent/manager acceptance.

Layer 9 remains the base guidance/expression layer. It should not directly absorb event anomalies as alpha or duplicate Layer 8 residual evidence.

## Manager Responsibilities

- Keep registered names aligned with this stack.
- Refuse requests that cross a layer boundary without a reviewed contract.
- Require receipts and ready signals before downstream consumption.
- Keep broker/account mutation outside manager and outside historical modeling services.
