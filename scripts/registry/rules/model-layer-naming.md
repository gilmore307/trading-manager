# Model Layer Registry Naming Rules

## Purpose

This file owns registry naming rules for model-layer source, feature, and model surfaces that cross repository boundaries.

It replaces dated watch-list notes with durable rules. Candidate names should be registered only when they become concrete SQL contracts, storage contracts, task receipts, model-facing payloads, or cross-repository handoffs.

## Canonical Surface Pattern

Use compact numeric layer prefixes:

```text
source_NN_<layer_slug>
feature_NN_<layer_slug>
model_NN_<layer_slug>
model_NN_<layer_slug>_explainability
model_NN_<layer_slug>_diagnostics
```

Accepted examples:

- `source_01_market_regime`
- `feature_01_market_regime`
- `model_01_market_regime`
- `model_01_market_regime_explainability`
- `model_01_market_regime_diagnostics`
- `source_02_target_candidate_holdings`
- `feature_02_sector_context`
- `model_02_sector_context`
- `source_03_strategy_selection`

Rules:

- `source_NN_*` rows are `data_source` when they are control-plane-facing runnable source outputs.
- `feature_NN_*` rows are `data_feature` when they are deterministic model-facing outputs produced by `trading-data`.
- `model_NN_*` names are model-owned contracts; register shared table/surface names as `term`, fields, statuses, or other appropriate kinds only when other repositories consume them.
- Do not maintain semantic aliases such as `layer01_*`, `layer02_*`, or separate prose-only route names for the same physical surface.

## Field Naming

Layer-owned fields use compact numeric prefixes only when the field is specific to that layer contract:

```text
1_*
2_*
3_*  # only after a Layer 3 contract is accepted for registry promotion
```

Generic identity, lineage, timestamp, receipt, run, and registry metadata fields should stay generic and should not receive a layer prefix.

Do not register generated feature columns merely because a model emits them. Register only durable fields that appear in a reviewed schema, task receipt, storage contract, or cross-repository handoff.

When a reviewed model contract makes a compact numeric-prefixed field the canonical downstream name, any active `field` row for that shared field should use the same compact payload. Do not leave downstream code split between an unprefixed registry field such as `price_behavior_factor` and a canonical physical/model field such as `1_price_behavior_factor`. If an unprefixed phrase is still useful as human concept language, keep it in notes or register it as a separate explanatory `term`, not as the canonical model-output `field`.

## Layer 2 Boundary

Layer 2 currently means market-state-conditioned sector/industry trend-stability and sector-context modeling.

Current accepted shared surfaces are:

- `source_02_target_candidate_holdings`
- `feature_02_sector_context`
- `model_02_sector_context`
- `sector_context_state`
- `target_candidate_id`
- `anonymous_target_feature_vector`

Human-readable ETF/sector behavior labels such as `growth`, `defensive`, `cyclical`, `inflation_sensitive`, and `safe_haven` are not prerequisite fixed registry classes. They may be post-hoc interpretations after Layer 2 evidence, but should not become hard-coded shared classes unless a reviewed output/status vocabulary requires them.

## Layer 3 Draft Boundary

Layer 3 design work may use draft StrategySelectionModel names such as `model_03_strategy_selection`, `3_strategy_family`, `3_strategy_variant`, and related `3_*` fields in `trading-model` contract drafts. Do not register those names merely because they appear in draft docs.

Layer 3 family-spec implementation may also use model-local draft parameter names such as `signal_bar_interval`, `unified_1min_bar_grid`, `ma_window_profile`, or other reviewed `*_profile` axes while the family/variant catalog is still being shaped. Treat these as local implementation-review vocabulary, not registry commitments, until a concrete SQL/storage/task handoff needs them.

Layer 3 monthly variant-lifecycle review may use model-local draft terms such as `active variant universe`, `training candidate subset`, `Universal Oracle`, `Theoretic Strategy Oracle`, `Practical Strategy Oracle`, and oracle-gap language. Keep these terms model-local until a reviewed manager-controlled lifecycle task, storage contract, or promotion workflow depends on them.

Accepted cross-repo handoff: manager-requested deterministic Layer 3 strategy selection feature production belongs to `trading-data` as `feature_03_strategy_selection`. `trading-manager` owns request generation/orchestration, `trading-data` owns deterministic per-bar family/variant simulation code inside `trading-data/src/data_feature/feature_03_strategy_selection/`, and `trading-model` owns oracle construction, variant lifecycle proposals, agent-reviewed expansion/pruning/promotion decisions, and StrategySelectionModel training.

Register Layer 3 model surfaces, support artifacts, compact fields, status vocabularies, parameter/profile axes, lifecycle/oracle review terms, or strategy-family/variant taxonomies only after the contract is accepted for cross-repository dependence or implementation needs a concrete SQL/storage/task handoff. The `feature_03_strategy_selection` data-feature name is accepted for that concrete handoff; remaining Layer 3 draft terms stay review-visible in `trading-model/docs/04_layer_03_strategy_selection.md` until promoted.

## Registration Trigger

Before implementation depends on a new shared model-layer name:

1. Decide whether it is a source, feature, model surface, field, classification/status value, table name, or explanatory term.
2. Reuse an accepted registered name when possible.
3. Add SQL migrations under `../sql/schema_migrations/` and regenerate `../current.csv` in the same change.
4. Do not register design-language placeholders or speculative basket states.
