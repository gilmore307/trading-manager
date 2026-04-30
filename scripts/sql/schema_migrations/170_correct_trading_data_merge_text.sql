-- Correct remaining text after the trading-data repository merge.

UPDATE trading_registry
SET
    payload = replace(replace(replace(payload,
        'trading-source', 'trading-data'),
        'trading-derived', 'trading-data'),
        'trading_source', 'trading_data'),
    path = replace(replace(replace(replace(path,
        'trading-source', 'trading-data'),
        'trading-derived', 'trading-data'),
        'data_sources', 'data_source'),
        'data_derived', 'data_feature'),
    applies_to = replace(replace(replace(replace(replace(applies_to,
        'trading-source', 'trading-data'),
        'trading-derived', 'trading-data'),
        'trading_source', 'trading_data'),
        'trading_derived', 'trading_data'),
        'derived_01_market_regime', 'feature_01_market_regime'),
    note = replace(replace(replace(replace(replace(replace(note,
        'trading-source', 'trading-data'),
        'trading-derived', 'trading-data'),
        'trading_source', 'trading_data'),
        'trading_derived', 'trading_data'),
        'derived_01_market_regime', 'feature_01_market_regime'),
        'derived feature', 'feature'),
    updated_at = CURRENT_TIMESTAMP
WHERE payload LIKE '%trading-source%'
   OR payload LIKE '%trading-derived%'
   OR payload LIKE '%trading_source%'
   OR path LIKE '%trading-source%'
   OR path LIKE '%trading-derived%'
   OR path LIKE '%data_sources%'
   OR path LIKE '%data_derived%'
   OR applies_to LIKE '%trading-source%'
   OR applies_to LIKE '%trading-derived%'
   OR applies_to LIKE '%trading_source%'
   OR applies_to LIKE '%trading_derived%'
   OR applies_to LIKE '%derived_01_market_regime%'
   OR note LIKE '%trading-source%'
   OR note LIKE '%trading-derived%'
   OR note LIKE '%trading_source%'
   OR note LIKE '%trading_derived%'
   OR note LIKE '%derived_01_market_regime%';
