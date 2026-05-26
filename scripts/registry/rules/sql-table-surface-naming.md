# SQL Table Surface Naming

This file owns shared rules for physical SQL table names and SQL-versus-artifact
storage boundaries when a surface crosses repository boundaries.

## Physical Name Pattern

SQL physical identifiers use lowercase snake_case. A dot separates only SQL
namespace levels, normally `schema.table`. Do not use hyphens in SQL schema,
table, column, registry, or task identifiers.

Canonical table names use:

```text
<schema>.<owner_prefix>_<domain_slug>_<task_stage>[_<artifact_role>]
```

Where:

- `schema` is the repository-owned SQL namespace, for example
  `trading_data`, `trading_model`, `trading_evaluation`, or
  `trading_execution`.
- `owner_prefix` is `mNN` for model-owned layer surfaces and `cNN` for
  execution component-owned surfaces. Layer-neutral governance, lifecycle,
  registry, receipt, and audit tables must not invent a fake layer or component
  number; they should carry layer/component refs in row fields when needed.
- `domain_slug` is the reviewed model, component, lifecycle, or data domain.
- `task_stage` is the task or lifecycle stage that creates the table.
- `artifact_role` is optional and names a support artifact such as
  `explainability`, `diagnostics`, or `contract_path`.

## Format Boundary

Use SQL for durable, queryable state:

- component decisions;
- model lifecycle decisions;
- runtime status;
- replay/fold/evaluation results;
- promotion, active-pointer, and elimination decisions;
- broker/order/account state once the relevant live gates are accepted;
- audit rows that must be filtered, joined, compared, or reviewed.

Use SQL plus artifact references for large payloads:

- realtime feature snapshots;
- model decision input snapshots;
- full provider capture payloads;
- large decision traces;
- detailed reports, charts, or explainability files.

The SQL row owns metadata, timing, ids, status, digests, and artifact refs. The
artifact owns the large payload. Artifact files must live outside Git-tracked
source paths under accepted storage contracts.

Use a SQL run row plus a receipt artifact for bounded operational receipts:

- smoke results;
- monitor loop receipts;
- capacity simulations;
- read-only live-observe receipts.

The SQL row records the run, status, safety flags, and artifact ref. The receipt
artifact may keep the larger structured detail.

Future-gated broker/order/fill/account/reconciliation tables may be named before
implementation for architecture clarity, but they are not active data surfaces
until their reviewed gates exist.

## Current Examples

Model/data surfaces:

```text
trading_data.m01_market_regime_data_acquisition
trading_data.m01_market_regime_feature_generation
trading_model.m01_market_regime_model_generation
trading_model.m01_market_regime_model_generation_explainability
trading_model.m01_market_regime_model_generation_diagnostics
```

Execution component surfaces:

```text
trading_execution.c01_intake_snapshot
trading_execution.c02_entry_decision
trading_execution.c03_position_lifecycle_decision
trading_execution.c04_option_reexpression_decision
trading_execution.c05_order_intent
trading_execution.c06_execution_gate_result
trading_execution.c07_failure_explanation_packet
trading_execution.c08_shadow_model_runtime_evidence
trading_execution.c08_shadow_cycle_selection
```

Layer-neutral evaluation and execution lifecycle surfaces:

```text
trading_evaluation.replay_execution_run
trading_evaluation.fold_settlement_run
trading_evaluation.promoted_model_parameter
trading_execution.realtime_feature_snapshot
trading_execution.execution_model_decision_input_snapshot
trading_execution.execution_active_model_config_write
```

Old `source_NN_*`, `feature_NN_*`, and `model_NN_*` names are migration debt,
not current planning names. Historical applied migrations may still mention old
names as immutable history.
