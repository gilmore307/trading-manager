# Architecture

This file is the manager-side map of the current M01-M05 model stack plus replay-review event attribution. It is a routing and boundary guide, not the model-design authority.

The event-impact probability-distribution and replay-review attribution
contract lives in `docs/31_event_impact_distribution.md`.

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
| M04 | `UnifiedDecisionModel` | `model_04_unified_decision`, `unified_decision_model` | Final direct-underlying posterior probability surface plus derived decision summary | `thesis_distribution_surface`, derived `unified_decision_vector` | Not broker routing, order construction, or account mutation. |
| M05 | `OptionExpressionModel` | `model_05_option_expression`, `option_expression_model` | Conditional option-expression payoff probability surface after M04 direct-underlying posterior | `expression_probability_surface`, derived `option_expression_plan` | Not execution and not broker/account mutation. |

## Physical Surface Rule

Active manager code, scripts, registry rows, SQL table names, storage paths, and docs use the current M01-M05 model numbers above. Event attribution and event-family governance are embedded in M03 event-state and replay-review diagnostics, not a separate model layer. SQL migration history is append-only audit material and is not rewritten by documentation cleanup.

## Event Path Rule

M03 owns the full fold-scoped point-in-time event universe before replay.
Replay review may inspect residual event evidence and abnormal activity only
after concentrated live-flow replay has exposed failures, residuals, misses, or
path deviations, and only as attribution against the fixed M03 ledger. M03/M04
may consume only accepted event evidence packets that passed point-in-time
checks, non-overlap checks, matched-control review, leakage review, and
agent/manager acceptance.
Shared event-feed coverage helpers are neutral source-coverage plumbing: their
row counts can prove local evidence availability, but they do not by themselves
complete M03 event-state substrate or perform replay-review event attribution.

M05 remains the optional option-expression layer. It should not directly absorb event anomalies as alpha or duplicate replay-review event-attribution evidence.

## Candidate Policy

M01 owns background context over broad market, sector, and industry state; it does not emit final target choices. M02 candidate handling is rule-fixed, not final-ticker-fixed: live routing builds candidates from the reviewed realtime total-symbol pool, target metadata, current hot/liquid market-wide names, and point-in-time liquidity, spread, data-quality, and optionability filters, then M02 ranks anonymous target-state candidates for handoff. Promotion replay uses the fixed `historical_candidate_universe.csv` table seeded from the current realtime equity pool plus the reviewed crypto spot candidate pool; it is stable replay scope, not point-in-time historical market-wide ranking evidence. A same-day candidate-universe freeze may be used for route smoke checks, but replay execution backs off until the accepted post-close readiness time so the final pool is not frozen during an active session. Downstream routes still own decision, option expression, replay-review diagnostics, and execution review.

Manager may schedule target-major substrate work because routing symbols only prepare data samples. That scheduling choice does not select the replay target. Live-flow replay must run the component graph against the fixed historical candidate pool, allowing components to choose no target, one target, or a target combination. A fixed-symbol run is a diagnostic repair scenario, not ordinary promotion evidence.

M03 event evidence has both reusable global/sector substrate and
target-local slices. Global/sector event-impact substrate belongs with
reusable foundation work, but it is still collected per fold because the
accepted observation pool can change across folds. Target-local event evidence
belongs with target substrate only when a downstream replay or diagnostic run
needs it.

## Manager Responsibilities

- Keep registered names aligned with this stack.
- Refuse requests that cross a layer boundary without a reviewed contract.
- Require receipts and ready signals before downstream consumption.
- Keep broker/account mutation outside manager and outside historical modeling services.
