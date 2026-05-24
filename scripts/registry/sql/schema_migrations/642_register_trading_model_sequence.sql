-- Register concise M01-M10 trading-model sequence names.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES (
  'cfg_TMODSEQ001',
  'config',
  'TRADING_MODEL_SEQUENCE',
  'text',
  'M01 Market Regime=model_01_market_regime;M02 Sector Context=model_02_sector_context;M03 Target State=model_03_target_state_vector;M04 Event Failure Risk=model_04_event_failure_risk;M05 Alpha Confidence=model_05_alpha_confidence;M06 Dynamic Risk Policy=model_06_dynamic_risk_policy;M07 Position Projection=model_07_position_projection;M08 Underlying Action=model_08_underlying_action;M09 Option Expression=model_09_option_expression;M10 Event Risk Governor=model_10_event_risk_governor',
  'trading-model/docs/02_architecture.md;trading-model/src/models/model_sequence.py',
  'trading-model;model_architecture;model_sequence;layers_01_10',
  'registry_only',
  'Accepted concise numbered model sequence. model_step/model_name are display and ordering fields; stable model_01 through model_10 package, script, SQL, and registry surfaces remain the contract-facing interface names.'
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
SET payload = 'current_physical_surfaces_aligned_with_ten_layer_order;m_prefixed_model_display_sequence;historical_migrations_and_artifacts_unchanged',
    note = 'Active script/table/package/stage names use stable model_01 through model_10 physical surfaces. M01 through M10 are concise display/order names only; they do not replace package, script, SQL table, or registry surface names. Historical/applied migrations and old artifacts remain unchanged for auditability.',
    updated_at = CURRENT_TIMESTAMP
WHERE id = 'cfg_LPNM001';
