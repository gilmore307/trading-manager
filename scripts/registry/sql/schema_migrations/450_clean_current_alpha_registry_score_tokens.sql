-- Complete current alpha-confidence registry score-token cleanup after the physical
-- current-version table/code migration. This leaves historical migrations/artifacts intact.

UPDATE trading_registry
SET payload = replace(replace(replace(payload,
        '5_alpha_direction_', '4_alpha_direction_'),
        '5_alpha_strength_', '4_alpha_strength_'),
        '5_alpha_confidence_', '4_alpha_confidence_'),
    note = replace(replace(replace(replace(note,
        'legacy 5_*', 'current 4_*'),
        'Legacy 5_*', 'Current 4_*'),
        'Physical value name remains current 5_* until dedicated migration.', 'Physical value name is current 4_* after current-version migration.'),
        'Accepted legacy 5_* AlphaConfidenceModel', 'Accepted current 4_* AlphaConfidenceModel'),
    updated_at = NOW()
WHERE payload LIKE '%5_alpha_direction_%'
   OR payload LIKE '%5_alpha_strength_%'
   OR payload LIKE '%5_alpha_confidence_%'
   OR note LIKE '%legacy 5_*%'
   OR note LIKE '%Legacy 5_*%';
