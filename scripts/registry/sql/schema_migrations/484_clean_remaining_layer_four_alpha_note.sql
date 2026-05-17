-- Clean one remaining post-insertion note that still called alpha confidence conceptual Layer 4.

UPDATE trading_registry
SET note = replace(note, 'conceptual Layer 4 alpha confidence', 'conceptual Layer 5 alpha confidence'),
    updated_at = NOW()
WHERE note LIKE '%conceptual Layer 4 alpha confidence%';
