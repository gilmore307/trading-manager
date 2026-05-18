-- Fix promotion acceptance receipt/status layer order after stable model-id migration.
-- Migration 512 replaced physical model_NN ids but preserved the previous
-- eight-entry layer sequence. The active nine-layer order requires explicit
-- EventFailureRiskModel Layer 4 and EventRiskGovernor Layer 9 entries.

UPDATE trading_registry
SET payload = 'layer_1:market_regime_model:mdevrun_1d00f2757982bd63:mpcand_b79411e80a774787:mpdec_d743cb5dbc8159f2:deferred;layer_2:sector_context_model:mdevrun_00c81e53569941df:mpcand_a6044e72162553f9:mpdec_3ab83ea1f423326d:deferred;layer_3:target_state_vector_model:mdevrun_327616bb447ceb5b:mpcand_1b077bca49a18dbf:mpdec_70fef0f31847cc1c:deferred;layer_4:event_failure_risk_model:mdevrun_closeout_l04_no_eval_substrate_20260508:mpcand_6ab73401f22ab057:mpdec_76b07ea01a3f525b:deferred;layer_5:alpha_confidence_model:mdevrun_closeout_l05_no_eval_substrate_20260508:mpcand_72289e5cc95ae2d5:mpdec_9c3e19d6559ef55b:deferred;layer_6:position_projection_model:mdevrun_closeout_l06_no_eval_substrate_20260508:mpcand_622c6ffa9ffca030:mpdec_b118232e76fae092:deferred;layer_7:underlying_action_model:mdevrun_closeout_l07_no_eval_substrate_20260508:mpcand_d4911cef39a14b97:mpdec_fabc9c709149a698:deferred;layer_8:option_expression_model:mdevrun_closeout_l08_no_eval_substrate_20260508:mpcand_9de333239d5c3f12:mpdec_e7448aaab1334345:deferred;layer_9:event_risk_governor:missing_production_eval_substrate:no_persisted_decision_receipt:deferred',
    note = 'Persisted promotion acceptance decision/status entries mapped to the current conceptual layer order. Layers with reviewed manager decisions keep their receipt ids; Layer 9 is explicitly deferred until a residual-event-risk production evaluation substrate and persisted review decision exist. Deferred decisions leave active config pointers unchanged.',
    updated_at = NOW()
WHERE key = 'MODEL_PROMOTION_ACCEPTANCE_DECISION_RECEIPTS';
