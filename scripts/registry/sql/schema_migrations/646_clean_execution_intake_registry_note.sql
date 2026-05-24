-- Clean remaining active registry wording after C01 intake narrowing.

UPDATE trading_registry
SET note = 'Execution runtime contract for independently funded account sleeves. Every execution intake snapshot, entry decision, position lifecycle decision, option re-expression decision, and execution order intent belongs to exactly one sleeve.',
    updated_at = CURRENT_TIMESTAMP
WHERE id = 'art_EXECRTC010';
