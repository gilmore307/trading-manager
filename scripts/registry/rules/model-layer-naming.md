# Model Layer Naming Rules

This file owns shared naming rules for model-layer source, feature, and model surfaces that cross repository boundaries.

## Current Layer Stack

| Layer | Boundary | Stable model id | Physical model surface |
|---|---|---|---|
| 1 | MarketRegimeModel | `market_regime_model` | `model_01_market_regime` |
| 2 | SectorContextModel | `sector_context_model` | `model_02_sector_context` |
| 3 | TargetStateVectorModel | `target_state_vector_model` | `model_03_target_state_vector` |
| 4 | EventFailureRiskModel | `event_failure_risk_model` | `model_04_event_failure_risk` |
| 5 | AlphaConfidenceModel | `alpha_confidence_model` | `model_05_alpha_confidence` |
| 6 | DynamicRiskPolicyModel | `dynamic_risk_policy_model` | `model_06_dynamic_risk_policy` |
| 7 | PositionProjectionModel | `position_projection_model` | `model_07_position_projection` |
| 8 | UnderlyingActionModel | `underlying_action_model` | `model_08_underlying_action` |
| 9 | TradingGuidanceModel / OptionExpressionModel | `option_expression_model` | `model_09_option_expression` |
| 10 | EventRiskGovernor / EventIntelligenceOverlay | `event_risk_governor` | `model_10_event_risk_governor` |

## Stable Id Rule

Use the stable model id for semantic interfaces: `model_id` fields, promotion targets, manager requests, completion/evaluation receipts, CLI `--model` arguments, scheduler/control-plane routing, and active registry payloads that name a model as an interface.

Use `model_NN_*` only for physical implementation surfaces: import/package paths, script paths, SQL table names, source/feature/model artifact surface names, physical-surface audit rows, and legacy-normalization migrations.

## SQL Table Surface Patterns

SQL physical identifiers use lowercase snake_case. A dot separates only SQL namespace levels, normally `schema.table`. Do not use hyphens in SQL table, column, schema, registry, or task identifiers; reserve hyphenated slugs for filesystem or URL surfaces that already require them.

New model/data table surfaces must use the current owner-domain-stage pattern:

```text
<schema>.<owner_prefix>_<domain_slug>_<task_stage>[_<artifact_role>]
```

Where:

- `owner_prefix` is `mNN` for model-owned layer surfaces and `cNN` for execution/component-owned surfaces.
- `domain_slug` is the reviewed model, component, or domain slug, for example `market_regime`.
- `task_stage` is the task that generates the table, for example `data_acquisition`, `feature_generation`, or `model_generation`.
- `artifact_role` is optional and names a support artifact such as `explainability` or `diagnostics`.

Examples:

```text
trading_data.m01_market_regime_data_acquisition
trading_data.m01_market_regime_feature_generation
trading_model.m01_market_regime_model_generation
trading_model.m01_market_regime_model_generation_explainability
trading_model.m01_market_regime_model_generation_diagnostics
```

Previously accepted layer-owned SQL tables used the older surface-stem pattern:

```text
source_NN_<surface_slug>
feature_NN_<surface_slug>
model_NN_<layer_slug>
model_NN_<layer_slug>_explainability
model_NN_<layer_slug>_diagnostics
```

Existing implemented `source_NN_*`, `feature_NN_*`, and `model_NN_*` tables remain explicit compatibility surfaces until a reviewed migration replaces them. Do not use the older pattern for newly planned tables.

For older `model_NN_*`, `NN` is the accepted model-layer number. For older `source_NN_*` and `feature_NN_*`, `NN` follows the registered data-source or feature-surface contract and must be checked against the row meaning. Layer-neutral governance, control-plane, registry, receipt, and audit tables must not invent a fake layer number; they should carry layer refs in row fields when needed.

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
feature_09_option_expression
source_10_event_risk_governor
```

Source-family numbers are not automatic proof of model-layer ownership. The registered row and accepted boundary decide ownership.

## Field Prefix Rule

Layer-owned model score tokens use compact numeric prefixes only when the token is part of a reviewed layer contract:

```text
1_* 2_* 3_* 4_* 5_* 6_* 7_* 8_* 9_* 10_*
```

Generic ids, refs, timestamps, run metadata, receipt metadata, and registry fields stay generic.

Core scalar score tokens that are shared across repositories belong in `state_vector_value`. Do not register every block name, diagnostic, enum, research payload, or generated column as a state-vector value.

## Boundary Rules

- Layer 1 conditions downstream work; it does not rank sectors, targets, strategies, positions, options, or actions.
- Layer 2 conditions target construction; it does not select final symbols or actions.
- Layer 3 builds target context; it does not emit alpha, exposure, option choice, or action.
- Layer 4 consumes only accepted event/strategy-failure evidence; it does not discover raw event families or trade.
- Layer 5 estimates adjusted alpha confidence; it does not size positions or choose instruments.
- Layer 6 produces dynamic risk policy state; it does not size positions, choose instruments, or emit broker orders.
- Layer 7 projects abstract holding state; it does not emit broker orders.
- Layer 8 produces offline direct-underlying thesis; it does not route orders or select option contracts.
- Layer 9 produces optional offline guidance/option-expression plans; it does not execute or mutate broker/account state.
- Layer 10 produces event-risk governance/intervention evidence from the Layer 8 direct-underlying thesis, with Layer 9 expression context optional; it may warn/block/cap/review/propose promotion but cannot trade or auto-promote.

## Registry Review Checklist

Before adding or changing a model-layer registry row, verify:

- the layer boundary is current;
- the row uses the narrowest kind;
- source/feature/model numbers are intentional;
- payload uses the stable id when it names a model interface, and the physical token only when it names a path/table/artifact surface;
- path points to the owning repo artifact when useful;
- no obsolete alias is kept only for convenience;
- tests and registry dry-run pass.
