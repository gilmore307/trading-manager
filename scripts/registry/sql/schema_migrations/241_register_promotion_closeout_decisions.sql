-- Register the 2026-05-08 promotion closeout decision receipts.
-- This records real deferred decisions and explicit blockers; it does not approve production activation.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'cfg_MPR002',
    'config',
    'MODEL_PROMOTION_READINESS_STATUS_MATRIX',
    'text',
    'layer_1_deferred_after_real_evaluation;layer_2_deferred_after_real_evaluation;layer_3_blocked_no_production_eval_run;layer_4_blocked_no_production_eval_run;layer_5_blocked_no_production_eval_run;layer_6_blocked_no_production_eval_run;layer_7_blocked_no_production_eval_run;layer_8_blocked_no_production_eval_run',
    'trading-model/docs/96_promotion_closeout.md',
    'model_governance;model_promotion;production_hardening;layers_1_8',
    'registry_only',
    'Current production-promotion closeout status after real database evidence was evaluated where available. Layers 1-2 have persisted deferred decisions; Layers 3-8 are blocked before promotion decision because no production evaluation run exists. No production activation is approved.'
  ),
  (
    'cfg_MPC001',
    'config',
    'MODEL_PROMOTION_CLOSEOUT_DECISION_RECEIPTS',
    'text',
    'layer_1:model_01_market_regime:mdevrun_1d00f2757982bd63:mpcand_b79411e80a774787:mpdec_d743cb5dbc8159f2:deferred;layer_2:model_02_sector_context:mdevrun_00c81e53569941df:mpcand_a6044e72162553f9:mpdec_3ab83ea1f423326d:deferred',
    'trading-model/docs/96_promotion_closeout.md',
    'model_governance;model_promotion;promotion_decision;promotion_closeout;layers_1_2',
    'registry_only',
    'Persisted promotion closeout decision receipts for layers with real database evaluation evidence. Deferred decisions leave active config pointers unchanged.'
  ),
  (
    'cfg_MPC002',
    'config',
    'MODEL_PROMOTION_CLOSEOUT_BLOCKERS',
    'text',
    'layer_1_failed_baseline_leakage_alignment_model_row_count_stability;layer_2_failed_baseline_improvement_split_stability;layers_3_8_no_production_eval_run',
    'trading-model/docs/96_promotion_closeout.md',
    'model_governance;model_promotion;promotion_blockers;layers_1_8',
    'registry_only',
    'Current blocker summary from the production-promotion closeout pass. These blockers prevent production approval or activation.'
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
