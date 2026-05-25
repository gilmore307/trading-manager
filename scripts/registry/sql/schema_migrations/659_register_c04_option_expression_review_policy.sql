-- Broaden C04 from held-option roll review to the full option/underlying expression translator.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES (
  'cfg_EXECRTC008',
  'config',
  'C04_OPTION_EXPRESSION_REVIEW_POLICY',
  'text',
  'translate_underlying_thesis_to_expression;consume_c02_c03_underlying_intent;consume_model_09_option_expression;single_leg_long_call_put_v1;underlying_only_fallback;no_valid_expression_status;no_position_sizing;no_broker_order;roll_only_when_materially_better',
  'trading-execution/docs/50_runtime_components.md;trading-model/docs/18_layer_09_trading_guidance.md',
  'component_04_option_review;option_reexpression_decision;entry_decision;position_lifecycle_decision;component_06_order_intent;model_09_option_expression;option_expression_plan;underlying_only_expression;no_option_expression',
  'sync_artifact',
  'C04 Option Review translates an accepted C02 entry thesis or C03 lifecycle intent into the best expression: long call, long put, underlying-only expression, or no valid option expression. It consumes Model 09 option-expression evidence and current option-chain context, checks DTE, delta/moneyness, IV, Greeks, spread/liquidity, fill quality, target/stop fit, and roll improvement. C04 does not decide whether the underlying thesis is valid, does not size positions, does not build broker orders, and does not mutate accounts. For held options, roll/re-expression requires the replacement contract to be materially better after liquidity, Greek, DTE, IV, and risk checks.'
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
SET note = 'Execution runtime contract emitted by C04 Option Review. It records the selected expression for an accepted C02 entry thesis or C03 lifecycle intent: long call, long put, underlying-only expression, no valid option expression, hold existing option, or roll/re-expression when a replacement contract is materially better after DTE, delta/moneyness, IV, Greek, liquidity, fill-quality, target/stop, and risk checks. It is not position sizing, not a broker order, and not account mutation.',
    updated_at = NOW()
WHERE key = 'OPTION_REEXPRESSION_DECISION';
