-- Register model-owned staged exposure adjustment and tactical add/reduce policy.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES (
  'cfg_TRCH001',
  'config',
  'TRANCHE_EXPOSURE_MANAGEMENT_POLICY',
  'text',
  'train_staged_entry_exit;train_risk_based_add_reduce;train_thesis_aware_high_sell_low_buy;no_ad_hoc_execution_scalping;model_07_projects_target_exposure_gap;model_08_owns_tranche_plan;component_03_uses_model_evidence_for_add_reduce;component_05_executes_current_tranche_quantity;component_06_must_not_change_quantity',
  'trading-model/docs/16_layer_07_position_projection.md;trading-model/docs/17_layer_08_underlying_action.md;trading-execution/docs/50_runtime_components.md',
  'model_07_position_projection;model_08_underlying_action;component_03_lifecycle;component_05_order_intent;component_06_execution_gate;tranche_plan;sizing_plan',
  'sync_artifact',
  'Accepted policy for staged exposure management. M07 trains target exposure and position-gap utility, including price-location and risk evidence. M08 owns tranche planning, risk-based add/reduce, and thesis-aware high-sell/low-buy style exposure adjustment. C03 may use those trained model outputs for lifecycle add/reduce decisions. C05 executes the current tranche as final order quantity. C06 validates/submits and must not change quantity. This is not an ad hoc scalping layer.'
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
  'fld_TRCH001',
  'field',
  'UNDERLYING_ACTION_TRANCHE_PLAN',
  'field_name',
  'tranche_plan',
  'trading-model/docs/17_layer_08_underlying_action.md',
  'underlying_action_plan;model_08_underlying_action;component_03_lifecycle;component_05_order_intent',
  'registry_only',
  'M08-owned plan describing the current staged entry/exit tranche, remaining target exposure, and conditions for later add/reduce tranches. It is strategy evidence for C03/C05 and not a broker order.'
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
SET note = 'C03 Lifecycle manages already-open positions in underlying-thesis terms. It decides hold, add, reduce, stop, exit, or take-profit from model stops, thesis invalidation, alpha, event risk, dynamic policy, position projection, and underlying action. Option contracts are expression translation owned by C04. Fixed option mark-to-market loss percentages are not ordinary lifecycle stops. C03 does not run fee, PDT, day-trade, or churn formulas; every non-hold action must carry explicit reason evidence. Add/reduce decisions may include risk-based tranche management and thesis-aware high-sell/low-buy exposure adjustment only when trained M07/M08 evidence supports them. Live submission requires C06 agent final review.',
    updated_at = NOW()
WHERE key = 'C03_LIFECYCLE_UNDERLYING_REVIEW_POLICY';

UPDATE trading_registry
SET note = 'C05 Order Intent owns all position-management content needed for an order: final quantity for the current tranche, target post-trade position/exposure when available, sizing reason codes, premium/capital-at-risk packaging through trade_risk_cap, and broker-neutral order policy. C05 does not decide whether to create staged entry/exit plans; it executes the current tranche from C03/C04/M08 evidence. C06 validates and executes the C05 intent but must not recalculate or modify quantity, target exposure, or order policy.',
    updated_at = NOW()
WHERE key = 'C05_ORDER_INTENT_POSITION_MANAGEMENT_POLICY';
