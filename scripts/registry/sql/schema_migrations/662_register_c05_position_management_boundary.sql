-- Make C05 the owner of final position sizing and order-intent construction.

UPDATE trading_registry
SET note = 'Broker-neutral execution intent emitted by C05 Order Intent from accepted entry, lifecycle, or option re-expression decisions before any live broker/account mutation gate. It carries the complete position-management result for the proposed operation: final quantity, target post-trade position when available, quantity source, sizing reason codes, broker-neutral order policy, and trade_risk_cap. C06 may reject or submit/simulate the intent, but must not recalculate or change quantity.',
    updated_at = NOW()
WHERE key = 'EXECUTION_ORDER_INTENT';

UPDATE trading_registry
SET note = 'C06 Execution Gate requires an approved Codex CLI final review before any live broker submission for open, add, reduce, exit, stop, take-profit, option roll, or stock fallback orders. The review is a missed-event guard: it checks whether current target, sector, macro, regulatory, filing, analyst, halt, earnings, or option-market events are absent from upstream C02/C03/C04/M10 evidence. C06 validates broker/regulatory hard blocks and submits or simulates the C05 order intent; it does not own position management, sizing, target exposure, or order-policy calculation.',
    updated_at = NOW()
WHERE key = 'EXECUTION_AGENT_FINAL_REVIEW_POLICY';

UPDATE trading_registry
SET note = 'Accepted concise numbered intraday execution component sequence. The normal live/replay order path is C01 Intake, C02 Entry, C03 Lifecycle, C04 Option Review, C05 Order Intent, and C06 Execution Gate. C05 owns final position-management and sizing content for the execution_order_intent. C06 only validates, reviews, and submits/simulates the C05 intent. C07 Failure Review is a post-failure branch only; it is not a normal pre-order step.',
    updated_at = NOW()
WHERE key = 'EXECUTION_RUNTIME_COMPONENT_SEQUENCE';

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES (
  'cfg_EXECRTC009',
  'config',
  'C05_ORDER_INTENT_POSITION_MANAGEMENT_POLICY',
  'text',
  'component_05_order_intent_owns_final_quantity;component_05_order_intent_owns_target_post_trade_position;component_05_order_intent_owns_sizing_reason_codes;component_05_order_intent_packages_trade_risk_cap;component_05_order_intent_builds_broker_neutral_order_policy;component_06_execution_gate_must_not_change_quantity;component_06_execution_gate_reject_or_submit_only;no_broker_mutation_in_c05',
  'trading-execution/docs/50_runtime_components.md;trading-execution/src/trading_execution/runtime/decisions.py',
  'component_05_order_intent;execution_order_intent;sizing_plan;trade_risk_cap;component_06_execution_gate',
  'sync_artifact',
  'C05 Order Intent owns all position-management content needed for an order: final quantity, target post-trade position/exposure when available, sizing reason codes, premium/capital-at-risk packaging through trade_risk_cap, and broker-neutral order policy. C06 validates and executes the C05 intent but must not recalculate or modify quantity, target exposure, or order policy.'
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
  'fld_EXECRTC012',
  'field',
  'EXECUTION_ORDER_INTENT_SIZING_PLAN',
  'field_name',
  'sizing_plan',
  'trading-execution/src/trading_execution/runtime/decisions.py;trading-execution/docs/50_runtime_components.md',
  'execution_order_intent;component_05_order_intent;component_06_execution_gate',
  'sync_artifact',
  'C05-owned execution_order_intent field carrying final quantity, quantity source, target post-trade position when available, planned exposure change, sizing reason codes, and the assertion that C06 may not change quantity.'
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
