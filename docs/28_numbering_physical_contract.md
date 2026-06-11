# Current Numbering and Physical-Name Contract

This file records the active numbering rule for manager-facing docs, scripts, SQL table names, storage paths, and registry rows.

## Current Model Numbers

| Model | Boundary | Physical token family |
|---|---|---|
| M01 | BackgroundContextModel | `model_01_background_context`, `background_context_model`, `background_context_state` |
| M02 | TargetStateModel | `model_02_target_state`, `target_state_model`, `target_context_state` |
| M03 | EventStateModel | `model_03_event_state`, `event_state_model`, `event_state_vector` |
| M04 | UnifiedDecisionModel | `model_04_unified_decision`, `unified_decision_model`, `unified_decision_vector` |
| M05 | OptionExpressionModel | `model_05_option_expression`, `option_expression_model`, `option_expression_plan` |
| M06 | ResidualEventGovernanceModel | `model_06_residual_event_governance`, `residual_event_governance_model`, `event_risk_intervention` |

## Rule

Active docs, code, tests, scripts, SQL table names, storage paths, and registry rows use the current M01-M06 physical tokens above. Immutable SQL migration history may contain older text because migrations are audit records.

## Review Check

Before accepting layer-numbering work, scan active docs/source/tests/scripts for stale route labels and verify registry dry-run has no pending migrations.
