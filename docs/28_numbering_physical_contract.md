# Current Numbering and Physical-Name Contract

This file records the active numbering rule for manager-facing docs, scripts, and registry rows.

## Current Layer Numbers

| Layer | Boundary | Physical token family |
|---|---|---|
| 1 | MarketRegimeModel | `layer_01_market_regime`, `market_regime_model`, `m01_market_regime_model_generation`, `model_01_market_regime` |
| 2 | SectorContextModel | `layer_02_sector_context`, `sector_context_model`, `m02_sector_context_model_generation`, `model_02_sector_context` |
| 3 | TargetStateVectorModel | `layer_03_target_state_vector`, `target_state_vector_model`, `model_03_target_state_vector` |
| 4 | EventFailureRiskModel | `layer_04_event_failure_risk`, `event_failure_risk_model`, `model_04_event_failure_risk` |
| 5 | AlphaConfidenceModel | `layer_05_alpha_confidence`, `alpha_confidence_model`, `model_05_alpha_confidence` |
| 6 | DynamicRiskPolicyModel | `layer_06_dynamic_risk_policy`, `dynamic_risk_policy_model`, `model_06_dynamic_risk_policy` |
| 7 | PositionProjectionModel | `layer_07_position_projection`, `position_projection_model`, `model_07_position_projection` |
| 8 | UnderlyingActionModel | `layer_08_underlying_action`, `underlying_action_model`, `model_08_underlying_action` |
| 9 | OptionExpressionModel | `layer_09_option_expression`, `option_expression_model`, `model_09_option_expression` |
| 10 | EventRiskGovernor | `layer_10_event_risk_governor`, `event_risk_governor`, `model_10_event_risk_governor` |

## Rule

Active docs, code, tests, scripts, and registry rows use the current 10-layer physical tokens above. Immutable SQL migration history may contain older text because migrations are audit records.

## Review Check

Before accepting layer-numbering work, scan active docs/source/tests/scripts for stale route labels and verify registry dry-run has no pending migrations.
