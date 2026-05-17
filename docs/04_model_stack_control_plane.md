# Model Stack Control Plane

This file is the manager-side map of the current Layer 1-9 stack. It is a routing and boundary guide, not the model-design authority.

## Stack Map

| Layer | Boundary | Main concept | Manager-facing handoff | Hard boundary |
|---|---|---|---|---|
| 1 | `MarketRegimeModel` | Broad-market context | `market_context_state` | No sector/target/action choice. |
| 2 | `SectorContextModel` | Sector/industry context | `sector_context_state` | No final symbol/action choice. |
| 3 | `TargetStateVectorModel` | Anonymous target context | `target_context_state` | No alpha, exposure, option, or action. |
| 4 | `EventFailureRiskModel` | Reviewed event/strategy-failure conditioning | `event_failure_risk_vector` | Consumes only accepted evidence packets; no action or execution. |
| 5 | `AlphaConfidenceModel` | Calibrated alpha confidence | `alpha_confidence_vector` | No exposure, option contract, or order. |
| 6 | `PositionProjectionModel` | Abstract holding-state projection | `position_projection_vector` | No buy/sell/hold order. |
| 7 | `UnderlyingActionModel` | Offline underlying thesis | `underlying_action_plan` | Not broker routing or order construction. |
| 8 | `TradingGuidanceModel / OptionExpressionModel` | Offline guidance and option-expression plan | `trading_guidance_record`, `option_expression_plan` | Not execution and not event-risk override. |
| 9 | `EventRiskGovernor / EventIntelligenceOverlay` | Residual event-risk review | `event_risk_intervention`, review/provenance/promotion packets | May warn/block/cap/review; cannot auto-promote or trade. |

## Physical Surface Rule

Active code, scripts, registry rows, and docs should use the current layer numbers above. SQL migration history is append-only audit material and is not rewritten by documentation cleanup.

## Event Path Rule

Layer 9 may inspect event evidence and residual abnormal activity. Layer 4 may consume only Layer 9 evidence packets that passed point-in-time checks, non-overlap checks, matched-control review, leakage review, and agent/manager acceptance.

Layer 8 remains the base guidance/expression layer. It should not directly absorb event anomalies as alpha or duplicate Layer 9 residual evidence.

## Manager Responsibilities

- Keep registered names aligned with this stack.
- Refuse requests that cross a layer boundary without a reviewed contract.
- Require receipts and ready signals before downstream consumption.
- Keep broker/account mutation outside manager and outside historical modeling services.
