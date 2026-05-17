# Numbering Physical Audit

Status: superseded by the 2026-05-17 conceptual Layer 04 insertion. This audit remains as historical evidence for the prior Layer 04-08 numbering cleanup; current physical names are now intentionally legacy until a dedicated code/SQL renumbering migration.

## Scope

This historical audit checked numbering after the 2026-05-15 conceptual layer reorder across:

- repository docs/code/script/test references;
- `trading-manager/scripts/registry/current.csv` generated registry content;
- local PostgreSQL `openclaw` table names, key columns, and sampled table content.

No scheduler/dashboard service was started, no provider calls were made, no model was activated, and no broker/account state was mutated.

## Current canonical conceptual order

| Conceptual layer | Canonical model boundary | Current physical-name posture |
| --- | --- | --- |
| 1 | `MarketRegimeModel` | current |
| 2 | `SectorContextModel` | current |
| 3 | `TargetStateVectorModel` | current |
| 4 | `EventFailureRiskModel` | governance/docs only; no renamed runtime package yet |
| 5 | `AlphaConfidenceModel` | legacy `model_04_alpha_confidence` |
| 6 | `PositionProjectionModel` | legacy `model_05_position_projection` |
| 7 | `UnderlyingActionModel` | legacy `model_06_underlying_action` |
| 8 | `TradingGuidanceModel / OptionExpressionModel` | legacy `model_07_option_expression` |
| 9 | `EventRiskGovernor / EventIntelligenceOverlay` | legacy `model_08_event_risk_governor` and `source_08_event_risk_governor` |

## Historical database table-name findings

The following findings described the 2026-05-16 state before the 2026-05-17 Layer 04 insertion. Those table names are now legacy physical surfaces. They must not be interpreted as approval to rename runtime packages or SQL tables in this governance-only slice.

| Current table | Rows observed | Conceptual owner | Recommended physical target |
| --- | ---: | --- | --- |
| `trading_model.model_08_event_risk_governor` | 62,458 | Layer 8 `EventRiskGovernor` | `trading_model.model_08_event_risk_governor` |
| `trading_model.model_04_alpha_confidence` | 63,780 | Layer 4 `AlphaConfidenceModel` | `trading_model.model_04_alpha_confidence` |
| `trading_model.model_05_position_projection` | 63,780 | Layer 5 `PositionProjectionModel` | `trading_model.model_05_position_projection` |
| `trading_model.model_06_underlying_action` | 63,780 | Layer 6 `UnderlyingActionModel` | `trading_model.model_06_underlying_action` |
| `trading_model.model_07_option_expression` | 63,780 | Layer 7 `TradingGuidanceModel / OptionExpressionModel` | `trading_model.model_07_option_expression` or a broader `trading_model.model_07_trading_guidance` surface after a naming decision |
| `trading_data.source_08_event_risk_governor` | 50,790 | legacy `source_08` event-risk source index; now conceptual Layer 9 physical surface | keep legacy name until a reviewed source/SQL renumbering decision |
| `trading_data.feature_08_event_risk_governor` | 49,696 | legacy `feature_08` event-risk feature handoff; now conceptual Layer 9 physical surface | keep legacy name until a reviewed feature/SQL renumbering decision |
| `trading_data.feature_07_option_expression` | not present in local SQL snapshot | Conceptual Layer 8 option-expression feature handoff | `trading_data.feature_07_option_expression` if/when physical feature surfaces are renamed |
| `trading_data.source_05_option_expression` | not present in local SQL snapshot | option-expression source id, not model layer id | keep unless source numbering policy changes |
| `trading_data.source_06_position_execution` | not present in local SQL snapshot | selected-contract replay/evaluation source id, not model layer id | keep unless source numbering policy changes |

## Database content findings

The following rows described the pre-insertion 2026-05-16 migrated state. After the 2026-05-17 Layer 04 insertion, these names are legacy physical surfaces and no longer imply conceptual alignment:

| Table | Column values observed | Row count |
| --- | --- | ---: |
| `trading_model.model_08_event_risk_governor` | `model_id=event_risk_governor`, `model_layer=layer_08_event_risk_governor` | 62,458 |
| `trading_model.model_04_alpha_confidence` | `model_id=alpha_confidence_model`, `model_layer=layer_04_alpha_confidence` | 63,780 |
| `trading_model.model_05_position_projection` | `model_id=position_projection_model`, `model_layer=layer_05_position_projection` | 63,780 |
| `trading_model.model_06_underlying_action` | `model_id=underlying_action_model`, `model_layer=layer_06_underlying_action` | 63,780 |
| `trading_model.model_07_option_expression` | `model_id=option_expression_model`, `model_layer=layer_07_option_expression` | 63,780 |
| `trading_data.feature_08_event_risk_governor` | `run_id` values such as `feature_08_event_risk_governor_2016-01`; `source_run_ref=source_08_event_risk_governor`; diagnostics `source_table=source_08_event_risk_governor` | 49,696 |
| `trading_data.source_08_event_risk_governor` | `source_name=source_08_event_risk_governor.equity_abnormal_activity`; file references containing `runs/layer_08_event_risk_governor_...` | 49,710+ matching rows |

The SQL/data migration lives at `scripts/current_table_migrations/001_align_current_layer_numbering.sql`; a pre-migration backup was captured before application.

## Registry content findings

`current.csv` still had mixed rows where notes said conceptual Layer 7/8 correctly but payloads or notes still used stale old-layer meaning. Examples corrected by the follow-up registry-note migration include:

- `OPTION_EXPRESSION_MODEL_LAYER_POLICY`: no longer says option expression is Layer 8; it is conceptual/current Layer 7.
- `OPTION_EXPRESSION_RESOLVED_FIELD_FAMILIES` and diagnostic families now use legacy `7_*` fields for conceptual Layer 8.
- `UNDERLYING_ACTION_*`: current conceptual Layer 6 score fields now use `6_*` prefixes.
- `BASE_ALPHA_VECTOR`: clarified as conceptual Layer 4 diagnostic context, not Layer 5/event-corrected alpha.
- `MODEL_PROMOTION_*` target lists: reordered notes/payloads to reflect the conceptual order.

## Follow-up fixes applied in this slice

- `trading-execution` realtime coverage still exposes legacy route keys (`layer_04_alpha_confidence`, `layer_05_position_projection`, `layer_06_underlying_action`, `layer_07_option_expression`, `layer_08_event_risk_governor`) until the reviewed execution-side renumbering migration.
- `trading-model` realtime decision handoff now routes the conceptual Layer 4-8 order with current generator entrypoint refs.
- `trading-manager` realtime shadow handoff and model-promotion request planning now use conceptual Layer 4-8 keys.
- Registry rows include `LAYER_PHYSICAL_NUMBERING_AUDIT`, updated promotion target ids, and resolved current-version numbering notes.

## Classification

### Current-version clean boundary

- Current conceptual model-stack docs are aligned to the nine-layer order.
- Current registry rows distinguish conceptual Layers 4-9 from legacy physical model/source/feature names.
- Current code/script/package paths under `trading-model`, `trading-data`, `trading-manager`, and `trading-execution` intentionally retain legacy numbering until a reviewed code/SQL renumbering migration.

### Intentionally unchanged historical surfaces

- Existing migration-history SQL may retain historical names.
- Existing storage artifact paths may retain historical run ids unless a storage-artifact migration is explicitly accepted.
- `source_05_option_expression` and `source_06_position_execution` are source ids, not model-layer ids; they are not automatically stale.
