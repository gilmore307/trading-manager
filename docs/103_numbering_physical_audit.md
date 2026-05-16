# Numbering Physical Audit

Status: active audit, 2026-05-16.

## Scope

This audit checks numbering after the 2026-05-15 conceptual layer reorder across:

- repository docs/code/script/test references;
- `trading-manager/scripts/registry/current.csv` generated registry content;
- local PostgreSQL `openclaw` table names, key columns, and sampled table content.

No scheduler/dashboard service was started, no provider calls were made, no model was activated, and no broker/account state was mutated.

## Canonical conceptual order

| Conceptual layer | Canonical model boundary |
| --- | --- |
| 1 | `MarketRegimeModel` |
| 2 | `SectorContextModel` |
| 3 | `TargetStateVectorModel` |
| 4 | `AlphaConfidenceModel` |
| 5 | `PositionProjectionModel` |
| 6 | `UnderlyingActionModel` |
| 7 | `TradingGuidanceModel / OptionExpressionModel` |
| 8 | `EventRiskGovernor / EventIntelligenceOverlay` |

## Database table-name findings

The local `openclaw` database still contains legacy physical table names for conceptual Layers 4-8. These are live SQL surfaces and should not be silently reclassified as clean just because docs mention the conceptual reorder.

| Current table | Rows observed | Conceptual owner | Recommended physical target |
| --- | ---: | --- | --- |
| `trading_model.model_04_event_overlay` | 62,458 | Layer 8 `EventRiskGovernor` | `trading_model.model_08_event_risk_governor` |
| `trading_model.model_05_alpha_confidence` | 63,780 | Layer 4 `AlphaConfidenceModel` | `trading_model.model_04_alpha_confidence` |
| `trading_model.model_06_position_projection` | 63,780 | Layer 5 `PositionProjectionModel` | `trading_model.model_05_position_projection` |
| `trading_model.model_07_underlying_action` | 63,780 | Layer 6 `UnderlyingActionModel` | `trading_model.model_06_underlying_action` |
| `trading_model.model_08_option_expression` | 63,780 | Layer 7 `TradingGuidanceModel / OptionExpressionModel` | `trading_model.model_07_option_expression` or a broader `trading_model.model_07_trading_guidance` surface after a naming decision |
| `trading_data.source_04_event_overlay` | 50,790 | Layer 8 event-risk source index | `trading_data.source_08_event_risk` or `trading_data.source_08_event_risk_governor` after a naming decision |
| `trading_data.feature_04_event_overlay` | 49,696 | Layer 8 event-risk feature handoff | `trading_data.feature_08_event_risk` or `trading_data.feature_08_event_risk_governor` after a naming decision |
| `trading_data.feature_08_option_expression` | not present in local SQL snapshot | Conceptual Layer 7 option-expression feature handoff | `trading_data.feature_07_option_expression` if/when physical feature surfaces are renamed |
| `trading_data.source_05_option_expression` | not present in local SQL snapshot | option-expression source id, not model layer id | keep unless source numbering policy changes |
| `trading_data.source_06_position_execution` | not present in local SQL snapshot | selected-contract replay/evaluation source id, not model layer id | keep unless source numbering policy changes |

## Database content findings

The table rows also carry legacy numbering in content, not just names:

| Table | Column values observed | Row count |
| --- | --- | ---: |
| `trading_model.model_04_event_overlay` | `model_id=event_overlay_model`, `model_layer=layer_04_event_overlay` | 62,458 |
| `trading_model.model_05_alpha_confidence` | `model_id=alpha_confidence_model`, `model_layer=layer_05_alpha_confidence` | 63,780 |
| `trading_model.model_06_position_projection` | `model_id=position_projection_model`, `model_layer=layer_06_position_projection` | 63,780 |
| `trading_model.model_07_underlying_action` | `model_id=underlying_action_model`, `model_layer=layer_07_underlying_action` | 63,780 |
| `trading_model.model_08_option_expression` | `model_id=option_expression_model`, `model_layer=layer_08_option_expression` | 63,780 |
| `trading_data.feature_04_event_overlay` | `run_id` values such as `feature_04_event_overlay_2016-01`; `source_run_ref=source_04_event_overlay`; diagnostics `source_table=source_04_event_overlay` | 49,696 |
| `trading_data.source_04_event_overlay` | `source_name=source_04_event_overlay.equity_abnormal_activity`; file references containing `runs/layer_04_event_overlay_...` | 49,710+ matching rows |

These values require a reviewed SQL/data migration if the project wants physical numbering fully aligned. Until then, code/docs must call them legacy physical surfaces, not current conceptual names.

## Registry content findings

`current.csv` still had mixed rows where notes said conceptual Layer 7/8 correctly but payloads or notes still used stale old-layer meaning. Examples corrected by the follow-up registry-note migration include:

- `OPTION_EXPRESSION_MODEL_LAYER_POLICY`: no longer says option expression is Layer 8; it is conceptual Layer 7, with legacy `layer_08_option_expression` physical tokens.
- `OPTION_EXPRESSION_RESOLVED_FIELD_FAMILIES`: clarified as legacy `8_*` fields for conceptual Layer 7.
- `UNDERLYING_ACTION_*`: clarified as conceptual Layer 6 while physical `7_*` fields remain legacy.
- `BASE_ALPHA_VECTOR`: clarified as conceptual Layer 4 diagnostic context, not Layer 5/event-corrected alpha.
- `MODEL_PROMOTION_*` target lists: reordered notes/payloads to reflect the conceptual order while preserving legacy physical ids until code/SQL migration.

## Follow-up fixes applied in this slice

- `trading-execution` realtime coverage now exposes conceptual `layer_04_alpha_confidence`, `layer_05_position_projection`, `layer_06_underlying_action`, `layer_07_option_expression`, and `layer_08_event_risk_governor` route keys. Legacy package/feature refs remain annotated as legacy physical paths.
- `trading-model` realtime decision handoff now routes the conceptual Layer 4-8 order while preserving legacy generator entrypoint refs until code/package migration.
- `trading-manager` realtime shadow handoff and model-promotion request planning now use conceptual Layer 4-8 keys. Promotion still accepts legacy physical model/layer aliases and records legacy evidence component ids for unmigrated evidence surfaces.
- Registry rows now include `LAYER_PHYSICAL_NUMBERING_AUDIT`, updated promotion target ids, and notes distinguishing conceptual numbering from legacy physical evidence ids.

## Classification

### Must migrate before claiming numbering is physically clean

- SQL table names listed above.
- SQL row `model_layer` values for conceptual Layers 4-8.
- SQL/data refs containing `feature_04_event_overlay`, `source_04_event_overlay`, `layer_04_event_overlay`, and legacy `model_05/06/07/08` model surfaces.
- Code/script/package paths under `trading-model/scripts/models/model_05_*`, `model_06_*`, `model_07_*`, and `model_08_option_expression` if physical naming is to match conceptual numbering.
- Realtime execution coverage rows in `trading-execution` that still expose legacy physical `model_layer` tokens.

### Accepted temporarily only with explicit legacy labeling

- `model_08_event_risk_governor` is already the correct conceptual Layer 8 event-risk implementation id.
- Existing migration-history SQL may retain historical names.
- Existing storage artifact paths may retain historical run ids unless a storage-artifact migration is explicitly accepted.
- `source_05_option_expression` and `source_06_position_execution` are source ids, not model-layer ids; they are ambiguous but not automatically stale.

## Recommended migration order

1. Decide final physical names for Layer 7 and event-risk data surfaces:
   - minimal: `model_07_option_expression`, `source_08_event_risk`, `feature_08_event_risk`;
   - broader: `model_07_trading_guidance` with option-expression as a sub-surface.
2. Rename code/packages/scripts/tests and update imports/entrypoints.
3. Add SQL/data migrations for table names, column names, `model_layer` values, score-prefix families, run ids, and manager/control-plane refs.
4. Update registry `current.csv` from migrations only.
5. Run full repo tests plus a read-only database consistency query proving no unclassified old numbering remains outside migration history and accepted storage artifacts.
