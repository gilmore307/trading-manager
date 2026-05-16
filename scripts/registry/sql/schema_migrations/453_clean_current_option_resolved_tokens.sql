-- Complete current option-expression resolved-field registry cleanup after the
-- current-version Layer 7 migration. Historical migrations/artifacts remain intact.

UPDATE trading_registry
SET payload = replace(payload, '8_resolved_', '7_resolved_'),
    note = replace(replace(note,
        'Reviewed legacy 8_* resolved expression field-family tokens for conceptual Layer 7',
        'Reviewed current 7_* resolved expression field-family tokens for conceptual Layer 7'),
        'legacy 8_*', 'current 7_*'),
    updated_at = NOW()
WHERE payload LIKE '%8_resolved_%'
   OR note LIKE '%legacy 8_*%';
