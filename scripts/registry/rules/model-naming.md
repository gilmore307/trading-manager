# Model Naming Rules

This file owns shared naming rules for model source, feature, and model surfaces that cross repository boundaries. General physical SQL table naming and SQL-versus-artifact storage boundaries live in `sql-table-surface-naming.md`.

## Current Model Stack

| Model | Boundary | Stable model id | Model-generation table |
|---|---|---|---|
| 1 | MarketRegimeModel | `market_regime_model` | `trading_model.model_01_market_regime_model_generation` |
| 2 | SectorContextModel | `sector_context_model` | `trading_model.model_02_sector_context_model_generation` |
| 3 | TargetStateVectorModel | `target_state_vector_model` | `trading_model.model_03_target_state_vector` |
| 4 | UnifiedDecisionModel | `unified_decision_model` | `trading_model.model_04_unified_decision` |
| 5 | OptionExpressionModel | `option_expression_model` | `trading_model.model_05_option_expression` |
| 6 | ResidualEventGovernanceModel | `residual_event_governance_model` | `trading_model.model_06_residual_event_governance` |

## Stable Id Rule

Use the stable model id for semantic interfaces: `model_id` fields, promotion targets, manager requests, completion/evaluation receipts, CLI `--model` arguments, scheduler/control-plane routing, and active registry payloads that name a model as an interface.

Use `model_NN_<domain_slug>_<task_stage>` SQL names for physical table surfaces. Implementation package and script paths may continue to use existing directory names until a reviewed source-path migration is scheduled; SQL table naming should not follow those package-path names.

## SQL Table Surface Patterns

Model/data table surfaces apply the shared pattern from
`sql-table-surface-naming.md`:

```text
<schema>.<owner_prefix>_<domain_slug>_<task_stage>[_<artifact_role>]
```

For model tables, `owner_prefix` is `model_NN`, `domain_slug` is the reviewed
model/domain slug, `task_stage` is the task that generates the table, and
`artifact_role` is optional support evidence such as `explainability` or
`diagnostics`.

Examples:

```text
trading_data.model_01_market_regime_data_acquisition
trading_data.model_01_market_regime_feature_generation
trading_model.model_01_market_regime_model_generation
trading_model.model_01_market_regime_model_generation_explainability
trading_model.model_01_market_regime_model_generation_diagnostics
```

Old `mNN_*`, `source_NN_*`, and `feature_NN_*` names are migration debt, not current planning names. Do not introduce, document, or register new tables with the old surface-stem pattern. Historical applied migrations may still mention old names as immutable history.

Model-neutral governance, control-plane, registry, receipt, and audit tables must not invent a fake model number; they should carry model refs in row fields when needed.

## Current Shared Table Examples

```text
trading_data.model_01_market_regime_data_acquisition
trading_data.model_01_market_regime_feature_generation
trading_model.model_01_market_regime_model_generation
trading_data.model_02_sector_context_data_acquisition
trading_data.model_02_sector_context_feature_generation
trading_data.model_03_target_state_vector_data_acquisition
trading_data.model_03_target_state_vector_feature_generation
trading_data.option_chain_state_source
trading_data.model_05_option_expression_feature_generation
trading_data.model_05_option_expression_data_acquisition_contract_path
trading_data.model_06_residual_event_governance_data_acquisition
trading_data.model_06_residual_event_governance_feature_generation
```

The table prefix is not automatic proof of business authority. The registered row and accepted boundary decide ownership.

## Field Prefix Rule

Model-owned model score tokens use compact numeric prefixes only when the token is part of a reviewed layer contract:

```text
1_* 2_* 3_* 4_* 5_* 6_*
```

Generic ids, refs, timestamps, run metadata, receipt metadata, and registry fields stay generic.

Core scalar score tokens that are shared across repositories belong in `state_vector_value`. Do not register every block name, diagnostic, enum, research payload, or generated column as a state-vector value.

## Boundary Rules

- M01 conditions downstream work; it does not rank sectors, targets, strategies, positions, options, or actions.
- M02 conditions target construction; it does not select final symbols or actions.
- M02 builds target context; it does not emit alpha, exposure, option choice, or action.
- M03 event-state produces the unified direct-underlying decision thesis; it does not route orders or mutate broker/account state.
- M04 decision produces optional offline option-expression plans; it does not execute or mutate broker/account state.
- M04 risk produces residual event governance/intervention evidence from the M04 thesis, with M05 expression context optional; it may warn/block/cap/review/propose promotion but cannot trade or auto-promote.

## Registry Review Checklist

Before adding or changing a model registry row, verify:

- the layer boundary is current;
- the row uses the narrowest kind;
- source/feature/model numbers are intentional;
- payload uses the stable id when it names a model interface, and the physical token only when it names a path/table/artifact surface;
- path points to the owning repo artifact when useful;
- no obsolete alias is kept only for convenience;
- tests and registry dry-run pass.
