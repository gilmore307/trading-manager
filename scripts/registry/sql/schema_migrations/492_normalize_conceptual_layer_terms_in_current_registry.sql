-- Normalize remaining active current registry note wording to the post-alignment layer names.
-- Historical migration files still preserve the older wording for audit history.

UPDATE trading_registry
SET note = replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(note,
      'conceptual Layer 4', 'Layer 4'),
      'Conceptual Layer 4', 'Layer 4'),
      'conceptual Layer 5', 'Layer 5'),
      'Conceptual Layer 5', 'Layer 5'),
      'conceptual Layer 6', 'Layer 6'),
      'Conceptual Layer 6', 'Layer 6'),
      'conceptual Layer 7', 'Layer 7'),
      'Conceptual Layer 7', 'Layer 7'),
      'conceptual Layer 8', 'Layer 8'),
      'Conceptual Layer 8', 'Layer 8'),
      'conceptual Layer 9', 'Layer 9'),
      'Conceptual Layer 9', 'Layer 9'),
    updated_at = NOW()
WHERE note LIKE '%conceptual Layer %'
   OR note LIKE '%Conceptual Layer %';
