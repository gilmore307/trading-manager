-- Normalize the public daily Layer 1 input-frame label to 1D.

UPDATE trading_registry
SET note = 'Layer 1/2 market-context ETF bar source. Downloads only canonical 1Min raw Alpaca bars into trading_data.source_01_market_regime; downstream feature_generation derives 1min, 10min, 1h, and 1D evidence locally. Provider-native multi-frame rows must not be mixed into this source table.',
    updated_at = CURRENT_TIMESTAMP
WHERE key = 'SOURCE_01_MARKET_REGIME';

UPDATE trading_registry
SET note = 'Layer 1 row identity field for the point-in-time input frame used to build market-state evidence, such as 1min, 10min, 1h, or 1D.',
    updated_at = CURRENT_TIMESTAMP
WHERE key = 'INPUT_FRAME';
