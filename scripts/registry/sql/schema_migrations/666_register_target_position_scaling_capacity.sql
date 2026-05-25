-- Register target-level buying-power capacity evidence for C03/C05 advanced
-- tranche management decisions.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES (
  'cfg_EXECRTC011',
  'config',
  'TARGET_POSITION_SCALING_CAPACITY_POLICY',
  'text',
  'target_allocated_buying_power_usd;estimated_unit_cost_usd;affordable_unit_count;min_advanced_position_management_units;single_allocation_no_advanced_scaling;advanced_tranche_management_allowed;protective_reductions_still_allowed',
  'trading-execution/docs/03_contracts.md;trading-execution/docs/50_runtime_components.md;trading-execution/src/trading_execution/runtime/decisions.py',
  'component_03_lifecycle;component_05_order_intent;execution_order_intent;sizing_plan;target_position_scaling_capacity',
  'sync_artifact',
  'Accepted execution policy for target-level position-scaling capacity. C03/C05 compare target-allocated buying power with estimated unit/contract cost. If the target can afford fewer than the minimum advanced-management units, tactical add/reduce and staged entry/exit optimization are skipped and C05 records single_allocation_no_advanced_scaling. Protective stops, exits, and risk-driven reductions remain allowed.'
)
ON CONFLICT (id) DO UPDATE SET
  kind = EXCLUDED.kind,
  key = EXCLUDED.key,
  payload_format = EXCLUDED.payload_format,
  payload = EXCLUDED.payload,
  path = EXCLUDED.path,
  applies_to = EXCLUDED.applies_to,
  artifact_sync_policy = EXCLUDED.artifact_sync_policy,
  note = EXCLUDED.note,
  updated_at = NOW();

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES (
  'fld_EXECRTC014',
  'field',
  'TARGET_POSITION_SCALING_CAPACITY',
  'field_name',
  'target_position_scaling_capacity',
  'trading-execution/src/trading_execution/runtime/decisions.py;trading-execution/docs/50_runtime_components.md',
  'execution_order_intent;sizing_plan;component_05_order_intent;component_03_lifecycle',
  'sync_artifact',
  'C05 sizing_plan field recording target-allocated buying power, estimated unit cost, affordable unit count, minimum advanced-management units, and whether advanced tranche management is allowed.'
)
ON CONFLICT (id) DO UPDATE SET
  kind = EXCLUDED.kind,
  key = EXCLUDED.key,
  payload_format = EXCLUDED.payload_format,
  payload = EXCLUDED.payload,
  path = EXCLUDED.path,
  applies_to = EXCLUDED.applies_to,
  artifact_sync_policy = EXCLUDED.artifact_sync_policy,
  note = EXCLUDED.note,
  updated_at = NOW();

UPDATE trading_registry
SET payload = 'component_05_order_intent_owns_final_quantity;component_05_order_intent_owns_target_post_trade_position;component_05_order_intent_owns_sizing_reason_codes;component_05_order_intent_packages_trade_risk_cap;component_05_order_intent_builds_broker_neutral_order_policy;component_05_records_target_position_scaling_capacity;component_06_execution_gate_must_not_change_quantity;component_06_execution_gate_reject_or_submit_only;no_broker_mutation_in_c05',
    note = 'C05 Order Intent owns all position-management content needed for an order: final quantity, target post-trade position/exposure when available, sizing reason codes, target position-scaling capacity, premium/capital-at-risk packaging through trade_risk_cap, and broker-neutral order policy. C06 emits execution_gate_result and routes the C05 intent but must not recalculate or modify quantity, target exposure, or order policy.',
    updated_at = NOW()
WHERE key = 'C05_ORDER_INTENT_POSITION_MANAGEMENT_POLICY';

UPDATE trading_registry
SET note = 'C03 Lifecycle manages already-open positions in underlying-thesis terms. It decides hold, add, reduce, stop, exit, or take-profit from model stops, thesis invalidation, alpha, event risk, dynamic policy, position projection, and underlying action. Option contracts are expression translation owned by C04. Fixed option mark-to-market loss percentages are not ordinary lifecycle stops. C03 does not run fee, PDT, day-trade, or churn formulas; every non-hold action must carry explicit reason evidence. Add/reduce decisions may include risk-based tranche management and thesis-aware high-sell/low-buy exposure adjustment only when trained M07/M08 evidence supports them and target position-scaling capacity can afford advanced management. Protective stops, exits, and risk-driven reductions remain allowed. Live submission requires C06 agent final review.',
    updated_at = NOW()
WHERE key = 'C03_LIFECYCLE_UNDERLYING_REVIEW_POLICY';

UPDATE trading_registry
SET payload = 'per_selected_target_dense_minute_training;train_staged_entry_exit;train_risk_based_add_reduce;train_thesis_aware_high_sell_low_buy;no_ad_hoc_execution_scalping;model_07_projects_target_exposure_gap;model_08_owns_tranche_plan;component_03_uses_model_evidence_for_add_reduce;component_05_executes_current_tranche_quantity;target_position_scaling_capacity_required_for_advanced_management;component_06_must_not_change_quantity',
    note = 'Accepted policy for staged exposure management. For each selected training target, M07/M08 train dense eligible minute sequences, including ordinary no-change, maintain, and no-trade minutes; they must not train only action-triggered minutes. The exclusion is only against all-market every-listed-symbol discovery scans, which belong upstream. M07 trains target exposure and position-gap utility, including price-location and risk evidence. M08 owns tranche planning, risk-based add/reduce, and thesis-aware high-sell/low-buy style exposure adjustment. C03 may use those trained model outputs for lifecycle add/reduce decisions only when target position-scaling capacity can afford advanced management. C05 executes the current tranche as final order quantity and records target capacity. C06 validates/submits and must not change quantity. This is not an ad hoc scalping layer.',
    updated_at = NOW()
WHERE key = 'TRANCHE_EXPOSURE_MANAGEMENT_POLICY';
