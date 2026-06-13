# Architecture

This file is the manager-side map of the current M01-M06 model stack. It is a routing and boundary guide, not the model-design authority.

## Module Map

| Docs band | Implementation surface | Purpose |
|---|---|---|
| `10_*` | `src/trading_registry/`, `scripts/registry/`, template surfaces | Registry and template authority. |
| `20_*` | `src/trading_manager_tasks/`, `scripts/tasks/`, scheduler/service definitions | Manager task system, historical planning, promotion, scheduler, and control-plane acceptance. |
| `30_*` | `src/trading_bigquery/`, `src/trading_web_search/`, shared helper policy | Shared helper package boundary. |

## Stack Map

| Model | Boundary | Physical token family | Main concept | Manager-facing handoff | Hard boundary |
|---|---|---|---|---|---|
| M01 | `BackgroundContextModel` | `model_01_background_context`, `background_context_model` | Broad market, sector, and industry background context | `background_context_state` | No target/action/option/event-family choice. |
| M02 | `TargetStateModel` | `model_02_target_state`, `target_state_model` | Anonymous target state and tradability context | `target_context_state` | No final action, sizing, or option contract. |
| M03 | `EventStateModel` | `model_03_event_state`, `event_state_model` | Accepted event-family exposure, uncertainty, and event-conditioned response context | `event_state_vector` | Does not mutate event-family identity, impact-window definitions, or action policy. |
| M04 | `UnifiedDecisionModel` | `model_04_unified_decision`, `unified_decision_model` | Direct-underlying utility decision, no-trade probability, exposure intent, and action heads | `unified_decision_vector` | Not broker routing, order construction, or account mutation. |
| M05 | `OptionExpressionModel` | `model_05_option_expression`, `option_expression_model` | Conditional option-expression context after M04 direct-underlying intent | `option_expression_plan` | Not execution and not broker/account mutation. |
| M06 | `ResidualEventGovernanceModel` | `model_06_residual_event_governance`, `residual_event_governance_model` | Residual event governance over the M04/M05 decision context after replay evidence | `event_risk_intervention`, review/provenance/promotion packets | May warn/block/cap/review; cannot auto-promote or trade. |

## Physical Surface Rule

Active code, scripts, registry rows, SQL table names, storage paths, and docs should use the current M01-M06 model numbers above. SQL migration history is append-only audit material and is not rewritten by documentation cleanup.

## Event Path Rule

M06 may inspect residual event evidence and abnormal activity only after
concentrated live-flow replay has exposed failures, residuals, misses, or path
deviations. It is not a pre-replay input stage. M03/M04 may consume only
accepted event evidence packets that passed point-in-time checks, non-overlap
checks, matched-control review, leakage review, and agent/manager acceptance.

M05 remains the optional option-expression layer. It should not directly absorb event anomalies as alpha or duplicate M06 residual evidence.

## Candidate Policy

M01 owns background context over broad market, sector, and industry state; it does not emit final target choices. M02 candidate handling is rule-fixed, not final-ticker-fixed: live routing builds candidates from the reviewed realtime total-symbol pool, target metadata, current hot/liquid market-wide names, and point-in-time liquidity, spread, data-quality, and optional optionability filters, then M02 ranks anonymous target-state candidates for handoff. Promotion replay uses the fixed `historical_candidate_universe.csv` table seeded from the current realtime pool plus BTC, ETH, and SOL; it is stable replay scope, not point-in-time historical market-wide ranking evidence. A same-day candidate-universe freeze may be used for route smoke checks, but replay execution backs off until the accepted post-close readiness time so the final pool is not frozen during an active session. Downstream models still own decision, option expression, residual event governance, and execution review.

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
