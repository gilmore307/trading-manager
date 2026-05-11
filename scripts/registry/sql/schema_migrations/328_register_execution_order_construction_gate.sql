-- Register gated broker order-intent construction.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'trm_EOC001',
    'term',
    'EXECUTION_ORDER_CONSTRUCTION_APPROVAL',
    'text',
    'execution_order_construction_approval_v1',
    'trading-execution/src/trading_execution/broker/order_construction.py',
    'trading-execution;broker_order_construction;trade_risk_cap;okx;no_broker_submission;no_account_mutation',
    'sync_artifact',
    'Reviewed approval artifact required before constructing a broker-shaped order intent. It does not authorize broker submission or account mutation.'
  ),
  (
    'trm_EOC002',
    'term',
    'EXECUTION_ORDER_CONSTRUCTION_APPROVAL_VALIDATION',
    'text',
    'execution_order_construction_approval_validation_v1',
    'trading-execution/src/trading_execution/broker/order_construction.py',
    'trading-execution;broker_order_construction;approval_validation;instrument_scope;side_scope;order_type_scope;expiry_check',
    'sync_artifact',
    'Validation result for broker order-construction approvals before an order intent can be built.'
  ),
  (
    'trm_EOC003',
    'term',
    'EXECUTION_BROKER_ORDER_INTENT',
    'text',
    'execution_broker_order_intent_v1',
    'trading-execution/src/trading_execution/broker/order_construction.py',
    'trading-execution;okx;broker_order_payload;idempotency_key;constructed_not_submitted;no_broker_submission;no_account_mutation',
    'sync_artifact',
    'Broker-shaped order intent produced after approval and trade-risk-cap validation. It is constructed but not submitted.'
  ),
  (
    'trm_EOC004',
    'term',
    'EXECUTION_BROKER_ORDER_INTENT_RESULT',
    'text',
    'execution_broker_order_intent_result_v1',
    'trading-execution/src/trading_execution/broker/order_construction.py',
    'trading-execution;broker_order_construction;approval_validation;risk_cap_validation;broker_order_intent',
    'sync_artifact',
    'Result envelope for broker order-intent construction, including approval validation, risk-cap validation, and the constructed intent when allowed.'
  ),
  (
    'scr_EOC001',
    'script',
    'EXECUTION_BROKER_ORDER_INTENT_BUILD',
    'command',
    'PYTHONPATH=src python3 scripts/execution/build_broker_order_intent.py --decision-record ${DECISION_RECORD_JSON} --approval ${APPROVAL_JSON} --construct-order',
    'trading-execution/scripts/execution/build_broker_order_intent.py',
    'trading-execution;execution_order_construction_approval_v1;execution_broker_order_intent_v1;trade_risk_cap;okx',
    'sync_artifact',
    'Constructs an approved OKX broker order intent without broker submission or account mutation.'
  ),
  (
    'cfg_EOC001',
    'config',
    'EXECUTION_ORDER_CONSTRUCTION_POLICY',
    'text',
    'order_intent_construction_requires_execution_order_construction_approval_v1_and_valid_trade_risk_cap;broker_submission_requires_separate_execution_gate;account_mutation_requires_separate_reconcile_gate',
    'trading-execution/docs/10_broker_interfaces.md',
    'trading-execution;broker_order_construction;broker_submission_gate;account_mutation_gate;risk_cap',
    'sync_artifact',
    'Policy separating approved broker order-intent construction from broker submission, fills, reconciliation, and account mutation.'
  )
ON CONFLICT (id) DO UPDATE
SET kind = EXCLUDED.kind,
    key = EXCLUDED.key,
    payload_format = EXCLUDED.payload_format,
    payload = EXCLUDED.payload,
    path = EXCLUDED.path,
    applies_to = EXCLUDED.applies_to,
    artifact_sync_policy = EXCLUDED.artifact_sync_policy,
    note = EXCLUDED.note,
    updated_at = NOW();
