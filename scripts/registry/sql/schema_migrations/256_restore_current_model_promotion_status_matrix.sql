-- Restore the latest accepted closeout wording for the promotion status matrix
-- after migration 255 recovered the row id from migration 254's config-id collision.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'cfg_MPR002',
    'config',
    'MODEL_PROMOTION_READINESS_STATUS_MATRIX',
    'text',
    'layer_1_deferred_after_real_evaluation;layer_2_deferred_after_real_evaluation;layer_3_real_production_eval_substrate_deferred_upstream_dependencies_and_calibration;layer_4_agent_reviewed_deferred_no_production_eval_substrate;layer_5_agent_reviewed_deferred_no_production_eval_substrate;layer_6_agent_reviewed_deferred_no_production_eval_substrate;layer_7_agent_reviewed_deferred_no_production_eval_substrate;layer_8_agent_reviewed_deferred_no_production_eval_substrate',
    'trading-model/docs/96_promotion_closeout.md',
    'model_governance;model_promotion;production_hardening;layers_1_8',
    'registry_only',
    'Current production-promotion closeout status after persisted decisions for every Layer 1-8 model. Layers 1-2 deferred after real database evaluation; Layer 3 deferred after real production-evaluation substrate because upstream dependencies and calibration are missing; Layers 4-8 deferred after reviewer-agent closeout because production evaluation substrate is missing. No production activation is approved.'
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
