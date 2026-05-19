-- Register post-generation model output quality gate entrypoint.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES (
  'scr_MOTQG001',
  'script',
  'MODEL_OUTPUT_QUALITY_GATE',
  'command',
  'PYTHONPATH=src python3 scripts/models/run_model_output_quality_gate.py --sample-limit 5000',
  '/root/projects/trading-model/scripts/models/run_model_output_quality_gate.py;/root/projects/trading-model/src/model_governance/model_output_quality_gate.py;/root/projects/trading-model/src/model_governance/model_output_audit.py;/root/projects/trading-model/docs/32_model_output_quality.md',
  'trading-model;trading_model.model_01_market_regime;trading_model.model_02_sector_context;trading_model.model_03_target_state_vector;trading_model.model_04_event_failure_risk;trading_model.model_05_alpha_confidence;trading_model.model_06_position_projection;trading_model.model_07_underlying_action;trading_model.model_08_option_expression;trading_model.model_09_event_risk_governor;model_output_quality_gate_v1;model_output_table_quality_audit_v1;post_generation_quality_gate',
  'sync_artifact',
  'Stable callable post-generation quality gate for all nine model output table families. It runs the read-only model output audit and exits non-zero when primary output defects such as missing/empty tables, all-null score columns, required ref gaps, support payload defects, or stale all-null primary columns should block acceptance. It performs no provider calls, SQL writes, column drops, model activation, broker/account mutation, or storage lifecycle mutation.'
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
