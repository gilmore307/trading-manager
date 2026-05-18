-- Align Layer 9 EventRiskGovernor registry notes with direct-underlying-first risk basis.

UPDATE trading_registry
SET applies_to = 'trading-model;trading-data;source_09_event_risk_governor;model_09_event_risk_governor;event_context_vector;event_risk_intervention;underlying_action_plan;trading_guidance_record;option_expression_plan;current_physical_names',
    note = 'Accepted Layer 9 event-risk governor. It consumes point-in-time residual event evidence with the Layer 7 direct-underlying action thesis as the canonical risk target; optional Layer 8 trading-guidance/option-expression context may be attached when available. It may warn/block/cap/review or emit promotion packets and remains bounded to risk governance unless reviewed evidence moves a family into Layer 4 EventFailureRiskModel.',
    updated_at = NOW()
WHERE id = 'trm_ERG001';

UPDATE trading_registry
SET note = 'Accepted canonical Layer 7 model id. UnderlyingActionModel maps alpha/position state plus point-in-time current/pending underlying exposure, quote/liquidity/borrow state, risk-budget state, and policy gates into an offline direct underlying planned action thesis for stock, ETF, or crypto spot-style candidates; current physical surface is model_07_underlying_action.',
    updated_at = NOW()
WHERE id = 'trm_UAM001';

UPDATE trading_registry
SET note = 'Layer 7 primary offline direct underlying planned action output for stock, ETF, or crypto spot-style candidates. It includes planned action type, effective exposure gap, planned incremental exposure, entry/target/stop/time-stop thesis, risk plan, Layer 8 trading-guidance handoff, and reason codes; it is not a broker/exchange order, final order quantity, option contract, or execution instruction.',
    updated_at = NOW()
WHERE id = 'trm_UAP001';

UPDATE trading_registry
SET note = 'Layer 7 score/vector output for direct underlying planned action quality by horizon. It carries eligibility, signed action direction, intensity, entry quality, expected return, adverse risk, reward/risk, liquidity fit, holding-time fit, and action confidence; it is not a broker/exchange order or option-expression vector.',
    updated_at = NOW()
WHERE id = 'trm_UAV001';

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES (
  'cfg_ERG002',
  'config',
  'EVENT_RISK_GOVERNOR_RISK_TARGET_BASIS',
  'text',
  'underlying_action_plan_primary;trading_guidance_record_optional;option_expression_plan_optional;crypto_direct_underlying_only',
  'trading-model/docs/18_layer_09_event_risk_governor.md',
  'event_risk_governor;underlying_action_plan;trading_guidance_record;option_expression_plan;crypto;direct_underlying_only',
  'sync_artifact',
  'Layer 9 EventRiskGovernor uses the Layer 7 direct-underlying/spot thesis as the canonical intervention target. Layer 8 trading-guidance and option-expression context are optional; crypto/direct-underlying-only routes must not require option-chain or option-expression evidence.'
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
