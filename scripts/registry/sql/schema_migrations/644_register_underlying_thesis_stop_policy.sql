-- Register high-risk options account stop-source policy.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES (
  'cfg_TRC004',
  'config',
  'UNDERLYING_THESIS_STOP_POLICY',
  'text',
  'high_risk_options_account_uses_model_underlying_stop;no_fixed_percentage_stop_substitution;option_mark_to_market_loss_not_primary_exit_trigger;premium_at_risk_sizes_capital_committed;missing_model_stop_rejects_order',
  'trading-execution/docs/10_trade_risk_cap.md;trading-execution/docs/05_decision.md;trading-execution/docs/50_runtime_components.md',
  'trade_risk_cap;component_03_lifecycle;component_04_option_review;component_07_execution_gate;model_08_underlying_action;model_09_option_expression;high_risk_options_account',
  'sync_artifact',
  'High-risk options account stop management is driven by model-provided underlying thesis invalidation and hard stop lines. Fixed percentage loss values may size risk budget and catastrophic account gates, but must not replace model stops for ordinary position management.'
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
    updated_at = CURRENT_TIMESTAMP;

UPDATE trading_registry
SET note = 'Shared term for the mandatory pre-order hard risk cap derived from model stop/invalidation thesis or option premium-defined risk. It is not itself a broker order. For the high-risk options account, option mark-to-market loss is not the primary exit trigger; model-provided underlying thesis invalidation and hard stop lines own ordinary stop management.',
    updated_at = CURRENT_TIMESTAMP
WHERE id = 'term_TRC001';

UPDATE trading_registry
SET note = 'Execution safety policy: any missing, malformed, unsupported, stale, or unenforceable trade_risk_cap must reject order construction/placement. Missing model stop or thesis-invalidation evidence must reject rather than falling back to a fixed percentage stop.',
    updated_at = CURRENT_TIMESTAMP
WHERE id = 'cfg_TRC003';
