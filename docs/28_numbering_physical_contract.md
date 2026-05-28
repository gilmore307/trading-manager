# Current Numbering and Physical-Name Contract

This file records the active numbering rule for manager-facing docs, scripts, and registry rows.

## Current Layer Numbers

| Layer | Boundary | Physical token family |
|---|---|---|
| 1 | MarketRegimeModel | `layer_01_market_regime`, `model_01_market_regime` |
| 2 | SectorContextModel | `layer_02_sector_context`, `model_02_sector_context` |
| 3 | TargetStateVectorModel | `layer_03_target_state_vector`, `model_03_target_state_vector` |
| 4 | EventFailureRiskModel | `layer_04_event_failure_risk`, `model_04_event_failure_risk` |
| 5 | AlphaConfidenceModel | `layer_05_alpha_confidence`, `model_05_alpha_confidence` |
| 6 | DynamicRiskPolicyModel | `layer_06_dynamic_risk_policy`, `model_06_dynamic_risk_policy` |
| 7 | PositionProjectionModel | `layer_07_position_projection`, `model_07_position_projection` |
| 8 | UnderlyingActionModel | `layer_08_underlying_action`, `model_08_underlying_action` |
| 9 | OptionExpressionModel | `layer_09_option_expression`, `model_09_option_expression` |
| 10 | EventRiskGovernor | `layer_10_event_risk_governor`, `model_10_event_risk_governor` |

## Rule

Active docs, code, tests, scripts, and registry rows use the current 10-layer physical tokens above. Immutable SQL migration history may contain older text because migrations are audit records.

## Review Check

Before accepting layer-numbering work, scan active docs/source/tests/scripts for stale route labels and verify registry dry-run has no pending migrations.
