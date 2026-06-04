# Architecture

This file is the manager-side map of the current Layer 1-10 stack. It is a routing and boundary guide, not the model-design authority.

## Module Map

| Docs band | Implementation surface | Purpose |
|---|---|---|
| `10_*` | `src/trading_registry/`, `scripts/registry/`, template surfaces | Registry and template authority. |
| `20_*` | `src/trading_manager_tasks/`, `scripts/tasks/`, scheduler/service definitions | Manager task system, historical planning, promotion, scheduler, and control-plane acceptance. |
| `30_*` | `src/trading_bigquery/`, `src/trading_web_search/`, shared helper policy | Shared helper package boundary. |

## Stack Map

| Layer | Boundary | Physical token family | Main concept | Manager-facing handoff | Hard boundary |
|---|---|---|---|---|---|
| 1 | `MarketRegimeModel` | `layer_01_market_regime`, `market_regime_model`, `m01_market_regime_model_generation`, `model_01_market_regime` | Broad-market context | `market_context_state` | No sector/target/action choice. |
| 2 | `SectorContextModel` | `layer_02_sector_context`, `sector_context_model`, `m02_sector_context_model_generation`, `model_02_sector_context` | Sector/industry context | `sector_context_state` | No final symbol/action choice. |
| 3 | `TargetStateVectorModel` | `layer_03_target_state_vector`, `target_state_vector_model`, `model_03_target_state_vector` | Anonymous target context and candidate ranking | `target_context_state`, `target_handoff_rank` | No alpha, exposure, option, position sizing, or final action. |
| 4 | `EventFailureRiskModel` | `layer_04_event_failure_risk`, `event_failure_risk_model`, `model_04_event_failure_risk` | Reviewed event/strategy-failure conditioning | `event_failure_risk_vector` | Consumes only accepted evidence packets; no action or execution. |
| 5 | `AlphaConfidenceModel` | `layer_05_alpha_confidence`, `alpha_confidence_model`, `model_05_alpha_confidence` | Calibrated alpha confidence | `alpha_confidence_vector` | No exposure, option contract, or order. |
| 6 | `DynamicRiskPolicyModel` | `layer_06_dynamic_risk_policy`, `dynamic_risk_policy_model`, `model_06_dynamic_risk_policy` | Dynamic risk-budget and premium-policy state from global market regime, systemic event risk, alpha quality, and portfolio context | `dynamic_risk_policy_state` | Not an execution hard-limit gate and not order permission. |
| 7 | `PositionProjectionModel` | `layer_07_position_projection`, `position_projection_model`, `model_07_position_projection` | Abstract holding-state projection under Layer 6 risk policy | `position_projection_vector` | No buy/sell/hold order. |
| 8 | `UnderlyingActionModel` | `layer_08_underlying_action`, `underlying_action_model`, `model_08_underlying_action` | Offline underlying thesis | `underlying_action_plan` | Not broker routing or order construction. |
| 9 | `OptionExpressionModel` | `layer_09_option_expression`, `option_expression_model`, `model_09_option_expression` | Optional offline option-expression context from the Layer 8 thesis | `option_expression_plan` | Not execution and not broker/account mutation. |
| 10 | `EventRiskGovernor` | `layer_10_event_risk_governor`, `event_risk_governor`, `model_10_event_risk_governor` | Residual event-risk governance over the Layer 8 direct-underlying thesis, with Layer 9 context optional | `event_risk_intervention`, review/provenance/promotion packets | May warn/block/cap/review; cannot auto-promote or trade. |

## Physical Surface Rule

Active code, scripts, registry rows, and docs should use the current layer numbers above. SQL migration history is append-only audit material and is not rewritten by documentation cleanup.

## Event Path Rule

Layer 10 may inspect residual event evidence and abnormal activity only after
concentrated live-flow replay has exposed failures, residuals, misses, or path
deviations. It is not a pre-replay input stage. Layer 4 may consume only Layer
10 evidence packets that passed point-in-time checks, non-overlap checks,
matched-control review, leakage review, and agent/manager acceptance.

Layer 9 remains the optional base guidance/expression layer. It should not directly absorb event anomalies as alpha or duplicate Layer 10 residual evidence.

## Layer 3 Candidate Policy

Layer 3 candidate generation is rule-fixed, not final-ticker-fixed. Live routing should build candidates from the reviewed realtime total-symbol pool, target metadata, current hot/liquid market-wide names, and point-in-time liquidity, spread, data-quality, and optional optionability filters. Promotion replay uses the fixed `historical_candidate_universe.csv` table seeded from the current realtime pool plus BTC, ETH, and SOL; it is stable replay scope, not point-in-time historical market-wide ranking evidence. A same-day candidate-universe freeze may be used for route smoke checks, but replay execution backs off until the accepted post-close readiness time so the final pool is not frozen during an active session. Layer 3 may rank the anonymous candidate-policy batch for target handoff, but downstream layers still own alpha confidence, action, sizing, option expression, and execution.

Manager may schedule target-major substrate work because routing symbols only prepare data samples. That scheduling choice does not select the replay target. Live-flow replay must run the component graph against the fixed historical candidate pool, allowing components to choose no target, one target, or a target combination. A fixed-symbol run is a diagnostic repair scenario, not ordinary promotion evidence.

Layer 4 event evidence has both reusable global/sector substrate and
target-local slices. Global/sector event-observation substrate belongs with
reusable foundation work, but it is still collected per fold because the
accepted observation pool can change across folds. Target-local event evidence
belongs with target substrate only when a downstream replay or diagnostic run
needs it.

## Manager Responsibilities

- Keep registered names aligned with this stack.
- Refuse requests that cross a layer boundary without a reviewed contract.
- Require receipts and ready signals before downstream consumption.
- Keep broker/account mutation outside manager and outside historical modeling services.
