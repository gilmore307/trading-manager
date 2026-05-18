-- Clean active score-family notes after the Layer 8/9 route correction.
-- Layer 6 owns position-projection 6_* score families.
-- Layer 8 owns option-expression 8_option_* score families.

UPDATE trading_registry
SET note = replace(note, 'Layer 9 high-is-good score family', 'Layer 8 high-is-good score family'),
    updated_at = NOW()
WHERE payload LIKE '8_option_%'
  AND note LIKE '%Layer 9 high-is-good score family%';

UPDATE trading_registry
SET note = replace(note, 'Layer 9 high-is-bad score family', 'Layer 8 high-is-bad score family'),
    updated_at = NOW()
WHERE payload LIKE '8_option_%'
  AND note LIKE '%Layer 9 high-is-bad score family%';

UPDATE trading_registry
SET note = replace(note, 'Reviewed Layer 5 diagnostic field-family tokens', 'Reviewed Layer 6 diagnostic field-family tokens'),
    updated_at = NOW()
WHERE payload LIKE '6_%'
  AND note LIKE '%Reviewed Layer 5 diagnostic field-family tokens%';

UPDATE trading_registry
SET note = replace(note, 'Layer 5 high-is-bad score family', 'Layer 6 high-is-bad score family'),
    updated_at = NOW()
WHERE payload LIKE '6_%'
  AND note LIKE '%Layer 5 high-is-bad score family%';

UPDATE trading_registry
SET note = replace(note, 'Layer 5 signed score family', 'Layer 6 signed score family'),
    updated_at = NOW()
WHERE payload LIKE '6_%'
  AND note LIKE '%Layer 5 signed score family%';
