-- Tighten remaining human-readable wording after renaming the Layer 1 deterministic
-- feature surface from derived_01_market_regime to feature_01_market_regime.

UPDATE trading_registry
SET
    note = replace(replace(replace(note,
        'derived features', 'feature definitions'),
        'derived feature', 'feature'),
        'derived table', 'feature table'),
    updated_at = CURRENT_TIMESTAMP
WHERE note LIKE '%derived feature%'
   OR note LIKE '%derived table%';
