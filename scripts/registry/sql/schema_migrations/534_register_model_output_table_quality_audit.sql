-- Register read-only model output table quality audit entrypoint.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES (
  'scr_MOTQA001',
  'script',
  'MODEL_OUTPUT_TABLE_QUALITY_AUDIT',
  'command',
  'PYTHONPATH=src python3 scripts/models/audit_model_output_tables.py --sample-limit 5000',
  '/root/projects/trading-model/scripts/models/audit_model_output_tables.py;/root/projects/trading-model/src/model_governance/model_output_audit.py;/root/projects/trading-model/docs/32_model_output_quality.md',
  'trading-model;trading_model.model_01_market_regime;trading_model.model_02_sector_context;trading_model.model_03_target_state_vector;trading_model.model_04_event_failure_risk;trading_model.model_05_alpha_confidence;trading_model.model_06_position_projection;trading_model.model_07_underlying_action;trading_model.model_08_option_expression;trading_model.model_09_event_risk_governor;model_output_table_quality_audit_v1;diagnostics;explainability',
  'sync_artifact',
  'Stable callable read-only audit for all nine model output table families, including primary, explainability, and diagnostics tables. It classifies empty and sparse columns as optional missing evidence, upstream data gaps, generator/support-table defects, or review-only cleanup candidates; it performs no provider calls, SQL writes, column drops, model activation, broker/account mutation, or storage lifecycle mutation.'
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
