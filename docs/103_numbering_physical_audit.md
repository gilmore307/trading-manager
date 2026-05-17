# Numbering Physical Audit

Status: superseded by the 2026-05-17 conceptual Layer 04 insertion. This audit remains as historical evidence for the prior Layer 04-08 numbering cleanup; current physical names are being aligned by the active code/SQL renumbering migration.

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
| 4 | `EventFailureRiskModel` | current physical scaffold |
| 5 | `AlphaConfidenceModel` | current `model_05_alpha_confidence` |
| 6 | `PositionProjectionModel` | current `model_06_position_projection` |
| 7 | `UnderlyingActionModel` | current `model_07_underlying_action` |
| 8 | `TradingGuidanceModel / OptionExpressionModel` | current `model_08_option_expression` |
| 9 | `EventRiskGovernor / EventIntelligenceOverlay` | current `model_09_event_risk_governor` and `source_09_event_risk_governor` |

## Historical database table-name findings

The following findings described the 2026-05-16 state before the 2026-05-17 Layer 04 insertion. Those observations are retained as pre-alignment evidence only. Active runtime packages and SQL tables now use the current nine-layer physical numbering recorded below.

| Current table | Rows observed | Conceptual owner | Recommended physical target |
| --- | ---: | --- | --- |
| `trading_model.model_09_event_risk_governor` | 62,458 | Layer 9 `EventRiskGovernor` after alignment | `trading_model.model_09_event_risk_governor` |
| `trading_model.model_05_alpha_confidence` | 63,780 | Layer 5 `AlphaConfidenceModel` after alignment | `trading_model.model_05_alpha_confidence` |
| `trading_model.model_06_position_projection` | 63,780 | Layer 6 `PositionProjectionModel` after alignment | `trading_model.model_06_position_projection` |
| `trading_model.model_07_underlying_action` | 63,780 | Layer 7 `UnderlyingActionModel` after alignment | `trading_model.model_07_underlying_action` |
| `trading_model.model_08_option_expression` | 63,780 | Layer 8 `TradingGuidanceModel / OptionExpressionModel` after alignment | `trading_model.model_08_option_expression` |
| `trading_data.source_09_event_risk_governor` | 50,790 | Layer 9 event-risk source index | current aligned source surface |
| `trading_data.feature_09_event_risk_governor` | 49,696 | Layer 9 event-risk feature handoff | current aligned feature surface |
| `trading_data.feature_08_option_expression` | not present in local SQL snapshot | Layer 8 option-expression feature handoff | `trading_data.feature_08_option_expression` |
| `trading_data.source_05_option_expression` | not present in local SQL snapshot | option-expression source id, not model layer id | keep unless source numbering policy changes |
| `trading_data.source_06_position_execution` | not present in local SQL snapshot | selected-contract replay/evaluation source id, not model layer id | keep unless source numbering policy changes |

## Database content findings

The following rows described the pre-insertion 2026-05-16 migrated state. After the 2026-05-17 Layer 04 insertion and active physical migration, these names are current aligned physical surfaces:

| Table | Column values observed | Row count |
| --- | --- | ---: |
| `trading_model.model_09_event_risk_governor` | `model_id=event_risk_governor`, `model_layer=layer_09_event_risk_governor` | 62,458 |
| `trading_model.model_05_alpha_confidence` | `model_id=alpha_confidence_model`, `model_layer=layer_05_alpha_confidence` | 63,780 |
| `trading_model.model_06_position_projection` | `model_id=position_projection_model`, `model_layer=layer_06_position_projection` | 63,780 |
| `trading_model.model_07_underlying_action` | `model_id=underlying_action_model`, `model_layer=layer_07_underlying_action` | 63,780 |
| `trading_model.model_08_option_expression` | `model_id=option_expression_model`, `model_layer=layer_08_option_expression` | 63,780 |
| `trading_data.feature_09_event_risk_governor` | `run_id` values such as `feature_09_event_risk_governor_2016-01`; `source_run_ref=source_09_event_risk_governor`; diagnostics `source_table=source_09_event_risk_governor` | 49,696 |
| `trading_data.source_09_event_risk_governor` | `source_name=source_09_event_risk_governor.equity_abnormal_activity`; file references containing `runs/layer_09_event_risk_governor_...` | 49,710+ matching rows |

The SQL/data migration lives at `scripts/current_table_migrations/001_align_current_layer_numbering.sql`; a pre-migration backup was captured before application.

## Registry content findings

`current.csv` still had mixed rows where notes used stale pre-alignment layer meaning or unclear conceptual/current wording. Examples corrected by the follow-up registry-note migration include:

- `OPTION_EXPRESSION_MODEL_LAYER_POLICY`: confirms option expression is current Layer 8.
- `OPTION_EXPRESSION_RESOLVED_FIELD_FAMILIES` and diagnostic families now use current `8_*` fields for Layer 8.
- `UNDERLYING_ACTION_*`: current Layer 7 score fields now use `7_*` prefixes.
- `BASE_ALPHA_VECTOR`: clarified as Layer 5 base-alpha diagnostic context, while Layer 4 owns event-failure-risk conditioning.
- `MODEL_PROMOTION_*` target lists: reordered notes/payloads to reflect the conceptual order.

## Follow-up fixes applied in this slice

- `trading-execution` realtime coverage still exposes legacy route keys (`layer_05_alpha_confidence`, `layer_06_position_projection`, `layer_07_underlying_action`, `layer_08_option_expression`, `layer_09_event_risk_governor`) until the reviewed execution-side renumbering migration.
- `trading-model` realtime decision handoff now routes the Layer 4-8 order with current generator entrypoint refs.
- `trading-manager` realtime shadow handoff and model-promotion request planning now use Layer 4-8 keys.
- Registry rows include `LAYER_PHYSICAL_NUMBERING_AUDIT`, updated promotion target ids, and resolved current-version numbering notes.

## Classification

### Current-version clean boundary

- Current conceptual model-stack docs are aligned to the nine-layer order.
- Current registry rows distinguish conceptual Layers 4-9 from current physical model/source/feature names.
- Current code/script/package paths under `trading-model`, `trading-data`, `trading-manager`, and `trading-execution` are being aligned by the reviewed code/SQL renumbering migration.

### Intentionally unchanged historical surfaces

- Existing migration-history SQL may retain historical names.
- Existing storage artifact paths may retain historical run ids unless a storage-artifact migration is explicitly accepted.
- `source_05_option_expression` and `source_06_position_execution` are source ids, not model-layer ids; they are not automatically stale.
