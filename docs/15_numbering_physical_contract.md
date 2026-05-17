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
| 6 | PositionProjectionModel | `layer_06_position_projection`, `model_06_position_projection` |
| 7 | UnderlyingActionModel | `layer_07_underlying_action`, `model_07_underlying_action` |
| 8 | TradingGuidanceModel / OptionExpressionModel | `layer_08_option_expression`, `model_08_option_expression` |
| 9 | EventRiskGovernor / EventIntelligenceOverlay | `layer_09_event_risk_governor`, `model_09_event_risk_governor` |

## Rule

Active docs, code, tests, scripts, and registry rows should use the current tokens above. Immutable SQL migration history may contain older text because migrations are audit records.

## Review Check

Before accepting layer-numbering work, scan active docs/source/tests/scripts for stale route labels and verify registry dry-run has no pending migrations.
