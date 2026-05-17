-- Register the SQL layer-table naming policy as a shared registry-backed naming rule.

INSERT INTO trading_registry (
  id,
  kind,
  key,
  payload_format,
  payload,
  path,
  applies_to,
  artifact_sync_policy,
  note
) VALUES (
  'cfg_SQLLTN001',
  'config',
  'SQL_LAYER_TABLE_NAMING_POLICY',
  'text',
  'layer_owned_sql_tables_use_source_NN_feature_NN_model_NN_prefixes;layer_neutral_governance_control_receipt_registry_audit_tables_stay_unnumbered;layer_refs_live_in_fields_for_neutral_tables',
  '/root/projects/trading-manager/scripts/registry/rules/model-layer-naming.md',
  'trading_data;trading_model;trading_manager;sql_table_naming;model_layer_naming;dashboard_data_tables',
  'sync_artifact',
  'Layer-owned SQL tables must expose the zero-padded model-layer number immediately after the surface stem, such as source_01_market_regime, feature_03_target_state_vector, and model_09_event_risk_governor. Layer-neutral governance/control/receipt/registry/audit tables must not invent fake layer prefixes; they carry layer references in fields when needed.'
)
ON CONFLICT (id) DO UPDATE SET
  key = EXCLUDED.key,
  payload_format = EXCLUDED.payload_format,
  payload = EXCLUDED.payload,
  path = EXCLUDED.path,
  applies_to = EXCLUDED.applies_to,
  artifact_sync_policy = EXCLUDED.artifact_sync_policy,
  note = EXCLUDED.note,
  updated_at = NOW();
