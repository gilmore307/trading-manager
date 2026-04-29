-- Align active bundle_05_option_expression registry fields with the accepted
-- contract-level SQL business table. The final table is one row per option
-- contract per entry/exit snapshot and no longer stores nested contracts JSON
-- or a contract_count business field.

DELETE FROM trading_registry
WHERE key IN ('OPTION_CONTRACT_COUNT', 'OPTION_CONTRACTS');

INSERT INTO trading_registry
  (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  ('fld_B05QTIM', 'temporal_field', 'QUOTE_TIMESTAMP', 'field_name', 'quote_timestamp', NULL, 'bundle_05_option_expression', 'sync_artifact', 'quote context timestamp for a contract-level option expression snapshot row'),
  ('fld_B05IVTM', 'temporal_field', 'IV_TIMESTAMP', 'field_name', 'iv_timestamp', NULL, 'bundle_05_option_expression', 'sync_artifact', 'implied-volatility context timestamp for a contract-level option expression snapshot row'),
  ('fld_B05GRTM', 'temporal_field', 'GREEKS_TIMESTAMP', 'field_name', 'greeks_timestamp', NULL, 'bundle_05_option_expression', 'sync_artifact', 'Greeks context timestamp for a contract-level option expression snapshot row'),
  ('fld_B05BEXC', 'field', 'QUOTE_BID_EXCHANGE', 'field_name', 'bid_exchange', NULL, 'bundle_05_option_expression', 'sync_artifact', 'ThetaData bid-side exchange code for a contract-level option expression snapshot row'),
  ('fld_B05AEXC', 'field', 'QUOTE_ASK_EXCHANGE', 'field_name', 'ask_exchange', NULL, 'bundle_05_option_expression', 'sync_artifact', 'ThetaData ask-side exchange code for a contract-level option expression snapshot row'),
  ('fld_B05BCND', 'field', 'QUOTE_BID_CONDITION', 'field_name', 'bid_condition', NULL, 'bundle_05_option_expression', 'sync_artifact', 'ThetaData bid-side quote condition code for a contract-level option expression snapshot row'),
  ('fld_B05ACND', 'field', 'QUOTE_ASK_CONDITION', 'field_name', 'ask_condition', NULL, 'bundle_05_option_expression', 'sync_artifact', 'ThetaData ask-side quote condition code for a contract-level option expression snapshot row')
ON CONFLICT (key) DO UPDATE
SET kind = EXCLUDED.kind,
    payload_format = EXCLUDED.payload_format,
    payload = EXCLUDED.payload,
    path = EXCLUDED.path,
    applies_to = EXCLUDED.applies_to,
    artifact_sync_policy = EXCLUDED.artifact_sync_policy,
    note = EXCLUDED.note,
    updated_at = now();
