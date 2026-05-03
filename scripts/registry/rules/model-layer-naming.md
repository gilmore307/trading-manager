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

## Registration Trigger

Before implementation depends on a new shared model-layer name:

1. Decide whether it is a source, feature, model surface, field, classification/status value, table name, or explanatory term.
2. Reuse an accepted registered name when possible.
3. Add SQL migrations under `../sql/schema_migrations/` and regenerate `../current.csv` in the same change.
4. Do not register design-language placeholders or speculative basket states.
