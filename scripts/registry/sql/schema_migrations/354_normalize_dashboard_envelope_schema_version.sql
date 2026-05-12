-- Align the dashboard common envelope with the stable-ID naming policy:
-- contract identity is contract_type; versioning is schema_version metadata.

UPDATE trading_registry
SET payload = replace(payload, 'contract_version', 'schema_version'),
    note = replace(note, 'contract_version', 'schema_version'),
    updated_at = NOW()
WHERE key = 'DASHBOARD_READ_MODEL_COMMON_ENVELOPE'
  AND (payload LIKE '%contract_version%' OR note LIKE '%contract_version%');
