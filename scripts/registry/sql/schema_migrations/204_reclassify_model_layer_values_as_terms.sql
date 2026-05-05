-- Model-layer classification tokens are shared terms, not lifecycle/status rows.
-- Keep status_value kind reserved for registered status domains such as
-- artifact_sync_policy_type.

UPDATE trading_registry
SET kind = 'term',
    payload_format = 'text',
    updated_at = CURRENT_TIMESTAMP
WHERE id IN ('mlv_L1MR001', 'mlv_L2SC001');
