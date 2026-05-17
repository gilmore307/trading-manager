# Model Layer Naming Rules

This file owns shared naming rules for model-layer source, feature, and model surfaces that cross repository boundaries.

## Current Layer Stack

| Layer | Boundary | Model surface |
|---|---|---|
| 1 | MarketRegimeModel | `model_01_market_regime` |
| 2 | SectorContextModel | `model_02_sector_context` |
| 3 | TargetStateVectorModel | `model_03_target_state_vector` |
| 4 | EventFailureRiskModel | `model_04_event_failure_risk` |
| 5 | AlphaConfidenceModel | `model_05_alpha_confidence` |
| 6 | PositionProjectionModel | `model_06_position_projection` |
| 7 | UnderlyingActionModel | `model_07_underlying_action` |
| 8 | TradingGuidanceModel / OptionExpressionModel | `model_08_option_expression` |
| 9 | EventRiskGovernor / EventIntelligenceOverlay | `model_09_event_risk_governor` |

## SQL Table Surface Patterns

Layer-owned SQL tables must put the zero-padded layer number directly after the surface stem:

```text
source_NN_<surface_slug>
feature_NN_<surface_slug>
model_NN_<layer_slug>
model_NN_<layer_slug>_explainability
model_NN_<layer_slug>_diagnostics
```

For `model_NN_*`, `NN` is the accepted model-layer number. For `source_NN_*` and `feature_NN_*`, `NN` follows the registered data-source or feature-surface contract and must be checked against the row meaning. Layer-neutral governance, control-plane, registry, receipt, and audit tables must not invent a fake layer number; they should carry layer refs in row fields when needed.

## Current Shared Source/Feature Examples

```text
source_01_market_regime
feature_01_market_regime
feature_02_sector_context
source_02_target_candidate_holdings
source_03_target_state
feature_03_target_state_vector
source_05_option_expression
source_06_position_execution
feature_08_option_expression
source_09_event_risk_governor
```

Source-family numbers are not automatic proof of model-layer ownership. The registered row and accepted boundary decide ownership.

## Field Prefix Rule

Layer-owned model score tokens use compact numeric prefixes only when the token is part of a reviewed layer contract:

```text
1_* 2_* 3_* 4_* 5_* 6_* 7_* 8_* 9_*
```

Generic ids, refs, timestamps, run metadata, receipt metadata, and registry fields stay generic.

Core scalar score tokens that are shared across repositories belong in `state_vector_value`. Do not register every block name, diagnostic, enum, research payload, or generated column as a state-vector value.

## Boundary Rules

- Layer 1 conditions downstream work; it does not rank sectors, targets, strategies, positions, options, or actions.
- Layer 2 conditions target construction; it does not select final symbols or actions.
- Layer 3 builds target context; it does not emit alpha, exposure, option choice, or action.
- Layer 4 consumes only accepted event/strategy-failure evidence; it does not discover raw event families or trade.
- Layer 5 estimates adjusted alpha confidence; it does not size positions or choose instruments.
- Layer 6 projects abstract holding state; it does not emit broker orders.
- Layer 7 produces offline direct-underlying thesis; it does not route orders or select option contracts.
- Layer 8 produces offline guidance/option-expression plans; it does not execute or override event governance.
- Layer 9 governs residual event risk; it may warn/block/cap/review/propose promotion but cannot trade or auto-promote.

## Registry Review Checklist

Before adding or changing a model-layer registry row, verify:

- the layer boundary is current;
- the row uses the narrowest kind;
- source/feature/model numbers are intentional;
- payload matches the accepted physical/contract token;
- path points to the owning repo artifact when useful;
- no obsolete alias is kept only for convenience;
- tests and registry dry-run pass.
