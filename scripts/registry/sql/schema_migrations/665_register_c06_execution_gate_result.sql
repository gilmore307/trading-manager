-- Register explicit C06 execution gate result between C05 order intent and
-- live/replay execution adapters.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES (
  'art_EXECRTC011',
  'artifact_type',
  'EXECUTION_GATE_RESULT',
  'text',
  'execution_gate_result',
  'trading-execution/docs/03_contracts.md;trading-execution/docs/50_runtime_components.md;trading-execution/src/trading_execution/runtime/components.py;trading-execution/src/trading_execution/runtime/decisions.py',
  'trading-execution;component_06_execution_gate;execution_order_intent;agent_final_review;execution_hard_block_checks;live;replay',
  'sync_artifact',
  'C06-owned execution gate artifact emitted after reviewing a C05 execution_order_intent. It records reject, approve-for-simulated-fill, or approve-for-live-submission outcomes, proves quantity is unchanged from the C05 sizing_plan, applies final hard-block checks, and requires approved agent final review before live broker submission.'
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
  'cfg_EXECRTC010',
  'config',
  'C06_EXECUTION_GATE_POLICY',
  'text',
  'component_06_execution_gate_owns_execution_gate_result;component_06_reject_or_route_only;component_06_must_not_change_quantity;component_06_must_not_change_order_policy;live_requires_approved_agent_final_review;replay_fill_requires_execution_gate_result;no_broker_or_account_mutation_in_default_gate_builder',
  'trading-execution/docs/03_contracts.md;trading-execution/docs/50_runtime_components.md;trading-execution/src/trading_execution/runtime/decisions.py',
  'component_06_execution_gate;execution_gate_result;execution_order_intent;simulated_fill_event;agent_final_review',
  'sync_artifact',
  'C06 Execution Gate owns final execution gating only. It may reject a C05 intent, approve it for Replay simulated fill, or approve it for live broker submission after agent final review, but it must not recalculate or modify quantity, target exposure, or broker-neutral order policy.'
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
  'fld_EXECRTC013',
  'field',
  'EXECUTION_GATE_RESULT_QUANTITY_UNCHANGED',
  'field_name',
  'quantity_unchanged_by_execution_gate',
  'trading-execution/src/trading_execution/runtime/decisions.py;trading-execution/docs/50_runtime_components.md',
  'execution_gate_result;component_06_execution_gate;execution_order_intent;sizing_plan',
  'sync_artifact',
  'C06 field proving the broker-neutral order quantity equals the C05 sizing_plan quantity and execution_gate_may_change_quantity remains false.'
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
SET note = 'Broker-neutral execution intent emitted by C05 Order Intent from accepted entry, lifecycle, or option re-expression decisions before any live broker/account mutation gate. It carries the complete position-management result for the proposed operation: final quantity, target post-trade position when available, quantity source, sizing reason codes, broker-neutral order policy, and trade_risk_cap. C06 must emit execution_gate_result before live submission or Replay fill simulation and must not recalculate or change quantity.',
    updated_at = NOW()
WHERE key = 'EXECUTION_ORDER_INTENT';

UPDATE trading_registry
SET note = 'Replay-only fill simulator event emitted after C06 approves an execution_gate_result for simulated fill. It cites both the source execution_order_intent and execution_gate_result, and never mutates a real broker or account.',
    updated_at = NOW()
WHERE key = 'SIMULATED_FILL_EVENT';

UPDATE trading_registry
SET note = 'C06 Execution Gate requires an approved Codex CLI final review before any live broker submission for open, add, reduce, exit, stop, take-profit, option roll, or stock fallback orders. The review is a missed-event guard: it checks whether current target, sector, macro, regulatory, filing, analyst, halt, earnings, or option-market events are absent from upstream C02/C03/C04/M10 evidence. C06 emits execution_gate_result, validates broker/regulatory hard blocks, and routes the C05 order intent, but it does not own position management, sizing, target exposure, or order-policy calculation.',
    updated_at = NOW()
WHERE key = 'EXECUTION_AGENT_FINAL_REVIEW_POLICY';

UPDATE trading_registry
SET note = 'C05 Order Intent owns all position-management content needed for an order: final quantity, target post-trade position/exposure when available, sizing reason codes, premium/capital-at-risk packaging through trade_risk_cap, and broker-neutral order policy. C06 emits execution_gate_result and routes the C05 intent but must not recalculate or modify quantity, target exposure, or order policy.',
    updated_at = NOW()
WHERE key = 'C05_ORDER_INTENT_POSITION_MANAGEMENT_POLICY';

UPDATE trading_registry
SET note = 'Accepted concise numbered intraday execution component sequence. The normal live/replay order path is C01 Intake, C02 Entry, C03 Lifecycle, C04 Option Review, C05 Order Intent, and C06 Execution Gate. C05 owns final position-management and sizing content for the execution_order_intent. C06 emits execution_gate_result, then rejects, approves live submission, or approves Replay simulation. C07 Failure Review is a post-failure branch only; it is not a normal pre-order step.',
    updated_at = NOW()
WHERE key = 'EXECUTION_RUNTIME_COMPONENT_SEQUENCE';
