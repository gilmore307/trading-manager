# SQL Table Surface Naming

This file owns shared rules for physical SQL table names and SQL-versus-artifact
storage boundaries when a surface crosses repository boundaries.

## Physical Name Pattern

SQL physical identifiers use lowercase snake_case. A dot separates only SQL
namespace levels, normally `schema.table`. Do not use hyphens in SQL schema,
table, column, registry, or task identifiers.

Model/data table names use:

```text
<schema>.<owner_prefix>_<domain_slug>_<task_stage>[_<artifact_role>]
```

Where:

- `schema` is the repository-owned SQL namespace, for example
  `trading_data`, `trading_model`, `trading_evaluation`, or
  `trading_execution`.
- `owner_prefix` is `model_NN` for model-owned layer surfaces.
- `domain_slug` is the reviewed model, component, lifecycle, or data domain.
- `task_stage` is the task or lifecycle stage that creates the table.
- `artifact_role` is optional and names a support artifact such as
  `explainability`, `diagnostics`, or `contract_path`.

Execution table names use business-family prefixes under `trading_execution`:

- `status_*` for runtime status, capabilities, and interface posture.
- `realtime_*` for realtime capture, feature snapshots, model-input snapshots,
  subscriptions, live-observe rows, and monitor receipts.
- `cNN_*` only for actual component-owned decision outputs.
- `trade_*` for risk, order-construction, broker-shaped intent rows, and
  future broker/account/position/fill/reconciliation rows.
- `performance_*` for live/shadow model performance, effectiveness,
  attribution, and lifecycle review evidence.

C08 raw runtime-performance rows are `performance_*` rows with model-group
identity fields such as `model_group_ref`, `model_group_role`, and
`model_group_run_ref`. The C08 component-owned SQL output is the cycle
selection table, for example `trading_execution.c08_shadow_cycle_selection`.

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
- read-only live-observe receipts.

The SQL row records the run, status, safety flags, and artifact ref. The receipt
artifact may keep the larger structured detail.

Capacity simulations are test artifacts unless a later reviewed runtime-capacity
task promotes them into a durable status or performance table.

Future-gated broker/order/fill/account/reconciliation tables may be named before
implementation for architecture clarity, but they are not active data surfaces
until their reviewed gates exist.

## Current Examples

Model/data surfaces:

```text
trading_data.model_01_market_regime_data_acquisition
trading_data.model_01_market_regime_feature_generation
trading_model.model_01_market_regime_model_generation
trading_model.model_01_market_regime_model_generation_explainability
trading_model.model_01_market_regime_model_generation_diagnostics
```

Execution status and realtime surfaces:

```text
trading_execution.status_realtime_trading_runtime
trading_execution.status_capability_catalog
trading_execution.status_realtime_data_interface
trading_execution.status_broker_interface
trading_execution.status_active_model_config_write
trading_execution.realtime_capture_contract
trading_execution.realtime_feature_snapshot
trading_execution.realtime_model_decision_input_snapshot
trading_execution.realtime_input_coverage
trading_execution.realtime_subscription_plan
trading_execution.realtime_live_observe_result
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
trading_execution.c08_shadow_cycle_selection
```

Execution trade and performance surfaces:

```text
trading_execution.trade_risk_cap
trading_execution.trade_order_construction_approval
trading_execution.trade_broker_order_intent
trading_execution.trade_broker_order_intent_result
trading_execution.trade_broker_order_submission
trading_execution.trade_broker_order_state
trading_execution.trade_broker_fill
trading_execution.trade_account_state_snapshot
trading_execution.trade_position_state_snapshot
trading_execution.trade_reconciliation_result
trading_execution.performance_model_runtime_evidence
trading_execution.performance_model_decision_effectiveness
trading_execution.performance_model_decision_effectiveness_row
trading_execution.performance_runtime_capacity_simulation
trading_execution.performance_runtime_model_lifecycle_review
```

Evaluation surfaces:

```text
trading_evaluation.replay_execution_run
trading_evaluation.fold_settlement_run
trading_evaluation.promoted_model_parameter
```

Old `mNN_*`, `source_NN_*`, and `feature_NN_*` names are migration debt, not
current planning names. Historical applied migrations may still mention old
names as immutable history.
