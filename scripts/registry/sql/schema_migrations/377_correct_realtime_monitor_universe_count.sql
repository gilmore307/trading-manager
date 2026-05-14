-- Correct realtime monitor universe wording after crypto proxy exclusions reduced the reviewed Layer 1/2 ETF universe to 44 rows.

UPDATE trading_registry
SET note = REPLACE(note, '47-symbol Layer 1/2 ETF universe', '44-symbol Layer 1/2 ETF universe'),
    updated_at = NOW()
WHERE note LIKE '%47-symbol Layer 1/2 ETF universe%';
