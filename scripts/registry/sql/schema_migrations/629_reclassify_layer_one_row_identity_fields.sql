-- input_frame, prediction_horizon, and market_universe_ref are row-identity
-- fields, not controlled classification axes.

UPDATE trading_registry
SET kind = 'identity_field',
    note = REPLACE(note, 'row-identity field', 'row identity field'),
    updated_at = CURRENT_TIMESTAMP
WHERE id IN ('fld_MRMFRAME', 'fld_MRMHORIZ', 'fld_MRMUNIV');
