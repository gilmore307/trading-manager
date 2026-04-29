UPDATE trading_registry
SET note = 'Curated Layer 1 V1 relative-strength combination table for MarketRegimeModel derived features. Rows define numerator/denominator ETF pairs, source bar grains, feature_bar_grain, combination_type, feature_type, and interpretation.',
    updated_at = CURRENT_TIMESTAMP
WHERE key = 'MARKET_REGIME_RELATIVE_STRENGTH_COMBINATIONS_SHARED_CSV';
