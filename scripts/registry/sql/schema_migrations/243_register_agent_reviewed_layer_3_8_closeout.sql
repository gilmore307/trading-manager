-- Register agent-reviewed Layer 3-8 production-promotion closeout decisions.
-- Layers 3-8 still have no production evaluation substrate; the important change is that
-- the blocker now flows through the same script -> reviewer-agent -> persisted-decision
-- route used for promotion closeout, with no activation.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'scr_MPC003',
    'script',
    'REVIEW_LAYERS_03_08_PROMOTION_CLOSEOUT',
    'text',
    'PYTHONPATH=src python3 scripts/models/review_layers_03_08_promotion_closeout.py --all --write-decision',
    'trading-model/scripts/models/review_layers_03_08_promotion_closeout.py',
    'model_governance;model_promotion;promotion_review;layers_3_8',
    'registry_only',
    'Stable callable promotion-closeout entrypoint for Layers 3-8. It builds blocked evaluation artifacts where production eval substrate is missing, calls the reviewer agent, persists the decision, and never activates deferred/rejected candidates.'
  ),
  (
    'cfg_MPR002',
    'config',
    'MODEL_PROMOTION_READINESS_STATUS_MATRIX',
    'text',
    'layer_1_deferred_after_real_evaluation;layer_2_deferred_after_real_evaluation;layer_3_agent_reviewed_deferred_no_production_eval_substrate;layer_4_agent_reviewed_deferred_no_production_eval_substrate;layer_5_agent_reviewed_deferred_no_production_eval_substrate;layer_6_agent_reviewed_deferred_no_production_eval_substrate;layer_7_agent_reviewed_deferred_no_production_eval_substrate;layer_8_agent_reviewed_deferred_no_production_eval_substrate',
    'trading-model/docs/96_promotion_closeout.md',
    'model_governance;model_promotion;production_hardening;layers_1_8',
    'registry_only',
    'Current production-promotion closeout status after persisted decisions for every Layer 1-8 model. Layers 1-2 deferred after real database evaluation; Layers 3-8 deferred after reviewer-agent closeout because production evaluation substrate is missing. No production activation is approved.'
  ),
  (
    'cfg_MPC001',
    'config',
    'MODEL_PROMOTION_CLOSEOUT_DECISION_RECEIPTS',
    'text',
    'layer_1:model_01_market_regime:mdevrun_1d00f2757982bd63:mpcand_b79411e80a774787:mpdec_d743cb5dbc8159f2:deferred;layer_2:model_02_sector_context:mdevrun_00c81e53569941df:mpcand_a6044e72162553f9:mpdec_3ab83ea1f423326d:deferred;layer_3:model_03_target_state_vector:mdevrun_closeout_l03_no_eval_substrate_20260508:mpcand_fffc92ba53b09199:mpdec_d8e027dd9b5aa939:deferred;layer_4:model_04_event_overlay:mdevrun_closeout_l04_no_eval_substrate_20260508:mpcand_6ab73401f22ab057:mpdec_76b07ea01a3f525b:deferred;layer_5:model_05_alpha_confidence:mdevrun_closeout_l05_no_eval_substrate_20260508:mpcand_72289e5cc95ae2d5:mpdec_9c3e19d6559ef55b:deferred;layer_6:model_06_position_projection:mdevrun_closeout_l06_no_eval_substrate_20260508:mpcand_622c6ffa9ffca030:mpdec_b118232e76fae092:deferred;layer_7:model_07_underlying_action:mdevrun_closeout_l07_no_eval_substrate_20260508:mpcand_d4911cef39a14b97:mpdec_fabc9c709149a698:deferred;layer_8:model_08_option_expression:mdevrun_closeout_l08_no_eval_substrate_20260508:mpcand_9de333239d5c3f12:mpdec_e7448aaab1334345:deferred',
    'trading-model/docs/96_promotion_closeout.md',
    'model_governance;model_promotion;promotion_decision;promotion_closeout;layers_1_8',
    'registry_only',
    'Persisted promotion closeout decision receipts for every Layer 1-8 model. Layers 3-8 receipts are reviewer-agent decisions from REVIEW_LAYERS_03_08_PROMOTION_CLOSEOUT. Deferred decisions leave active config pointers unchanged.'
  ),
  (
    'cfg_MPC002',
    'config',
    'MODEL_PROMOTION_CLOSEOUT_BLOCKERS',
    'text',
    'layer_1_failed_baseline_leakage_alignment_model_row_count_stability;layer_2_failed_baseline_improvement_split_stability;layers_3_8_agent_reviewed_missing_production_eval_run_labels_metrics',
    'trading-model/docs/96_promotion_closeout.md',
    'model_governance;model_promotion;promotion_blockers;layers_1_8',
    'registry_only',
    'Current blocker summary from the production-promotion closeout pass. Layers 3-8 blockers were reviewed by the promotion reviewer agent and prevent production approval or activation.'
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
