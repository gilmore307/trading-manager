-- Keep the market-context source policy notes ASCII after migration 630 was
-- applied with typographic apostrophes in two field notes.

UPDATE trading_registry
SET note = 'Numerator ETF source-observation cue retained for reviewed relative-strength metadata. Market-context acquisition still downloads canonical 1Min bars; downstream feature_generation derives this row''s feature grain locally.',
    updated_at = CURRENT_TIMESTAMP
WHERE key = 'NUMERATOR_BAR_GRAIN';

UPDATE trading_registry
SET note = 'Denominator ETF source-observation cue retained for reviewed relative-strength metadata. Market-context acquisition still downloads canonical 1Min bars; downstream feature_generation derives this row''s feature grain locally.',
    updated_at = CURRENT_TIMESTAMP
WHERE key = 'DENOMINATOR_BAR_GRAIN';
