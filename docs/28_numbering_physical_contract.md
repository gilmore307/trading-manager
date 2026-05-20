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
| 7 | PositionProjectionModel | `layer_07_position_projection`, physical `model_06_position_projection` until renumbering |
| 8 | UnderlyingActionModel | `layer_08_underlying_action`, physical `model_07_underlying_action` until renumbering |
| 9 | TradingGuidanceModel / OptionExpressionModel | `layer_09_option_expression`, physical `model_08_option_expression` until renumbering |
| 10 | EventRiskGovernor / EventIntelligenceOverlay | `layer_10_event_risk_governor`, physical `model_09_event_risk_governor` until renumbering |

## Rule

Active docs, code, tests, scripts, and registry rows should use the current conceptual layer tokens above. Physical implementation tokens may temporarily retain prior Layer 6-9 numbering where explicitly marked until dedicated renumbering. Immutable SQL migration history may contain older text because migrations are audit records.

## Review Check

Before accepting layer-numbering work, scan active docs/source/tests/scripts for stale route labels and verify registry dry-run has no pending migrations.
