# Current Numbering and Physical-Name Contract

This file records the active numbering rule for manager-facing docs, scripts,
SQL table names, storage paths, and registry rows.

## Current Model Numbers

| Model | Boundary | Physical token family |
|---|---|---|
| M01 | BackgroundContextModel | `model_01_background_context`, `background_context_model`, `background_context_state` |
| M02 | TargetStateModel | `model_02_target_state`, `target_state_model`, `target_context_state` |
| M03 | EventStateModel | `model_03_event_state`, `event_state_model`, `event_state_vector` |
| M04 | UnifiedDecisionModel | `model_04_unified_decision`, `unified_decision_model`, `thesis_distribution_surface`, derived `unified_decision_vector` |
| M05 | OptionExpressionModel | `model_05_option_expression`, `option_expression_model`, `option_expression_plan` |

## Compatibility Physical Tokens

`model_06_residual_event_governance`, `residual_event_governance_model`, and
`event_risk_intervention` may still appear in registry rows, SQL/source storage
paths, and cross-repository physical artifacts until those owning repositories
complete their own migration. They are compatibility physical names, not an
independent manager model/task lane.

## Rule

Active manager workflow, scheduler, promotion, and dashboard surfaces use the
current M01-M05 model stack. Replay review owns post-replay event attribution
as an embedded diagnostic surface, while M03 owns pre-replay event-state and
event-family modelability. Immutable SQL migration history may contain older
text because migrations are audit records.

## Review Check

Before accepting layer-numbering work, scan active docs/source/tests/scripts for stale route labels and verify registry dry-run has no pending migrations.
