# Current Numbering and Physical-Name Contract

This file records the active numbering rule for manager-facing docs, scripts,
SQL table names, storage paths, and registry rows.

## Current Model Numbers

| Model | Boundary | Physical token family |
|---|---|---|
| M01 | BackgroundContextModel | `model_01_background_context`, `background_context_model`, `background_context_state` |
| M02 | TargetStateModel | `model_02_target_state`, `target_state_model`, `target_context_state` |
| M03 | EventStateModel | `model_03_event_state`, `event_state_model`, `event_state_vector`, `event_effect_model` |
| M04 | UnifiedDecisionModel | `model_04_unified_decision`, `unified_decision_model`, `thesis_distribution_surface`, derived `unified_decision_vector` |
| M05 | OptionExpressionModel | `model_05_option_expression`, `option_expression_model`, `expression_probability_surface`, derived `option_expression_plan` |

## Rule

Active manager workflow, scheduler, promotion, dashboard, registry, and docs
use the current M01-M05 model stack. M03 owns event-state and event-family
modelability. Replay review owns post-replay event attribution as an embedded
diagnostic surface. Component event-risk control is operational behavior, not a
model layer.

Immutable SQL migration history may contain older text because migrations are
audit records.

## Review Check

Before accepting layer-numbering work, scan active docs/source/tests/scripts for
stale route labels and verify registry dry-run has no pending migrations.
