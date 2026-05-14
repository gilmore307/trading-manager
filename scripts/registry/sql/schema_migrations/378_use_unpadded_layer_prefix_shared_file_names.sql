-- Align shared CSV file paths with the accepted unpadded layer_1_ / layer_2_ filename convention.

UPDATE trading_registry
SET payload = REPLACE(payload, 'layer_01_02_market_context_etf_universe.csv', 'layer_1_2_market_context_etf_universe.csv'),
    updated_at = NOW()
WHERE payload LIKE '%layer_01_02_market_context_etf_universe.csv%';

UPDATE trading_registry
SET path = REPLACE(path, 'layer_01_02_market_context_etf_universe.csv', 'layer_1_2_market_context_etf_universe.csv'),
    updated_at = NOW()
WHERE path LIKE '%layer_01_02_market_context_etf_universe.csv%';

UPDATE trading_registry
SET note = REPLACE(note, 'layer_01_02_market_context_etf_universe.csv', 'layer_1_2_market_context_etf_universe.csv'),
    updated_at = NOW()
WHERE note LIKE '%layer_01_02_market_context_etf_universe.csv%';

UPDATE trading_registry
SET payload = REPLACE(payload, 'layer_01_02_market_context_relative_strength_combinations.csv', 'layer_1_2_market_context_relative_strength_combinations.csv'),
    updated_at = NOW()
WHERE payload LIKE '%layer_01_02_market_context_relative_strength_combinations.csv%';

UPDATE trading_registry
SET path = REPLACE(path, 'layer_01_02_market_context_relative_strength_combinations.csv', 'layer_1_2_market_context_relative_strength_combinations.csv'),
    updated_at = NOW()
WHERE path LIKE '%layer_01_02_market_context_relative_strength_combinations.csv%';

UPDATE trading_registry
SET note = REPLACE(note, 'layer_01_02_market_context_relative_strength_combinations.csv', 'layer_1_2_market_context_relative_strength_combinations.csv'),
    updated_at = NOW()
WHERE note LIKE '%layer_01_02_market_context_relative_strength_combinations.csv%';

UPDATE trading_registry
SET payload = REPLACE(payload, 'layer_02_target_context_mapping.csv', 'layer_2_target_context_mapping.csv'),
    updated_at = NOW()
WHERE payload LIKE '%layer_02_target_context_mapping.csv%';

UPDATE trading_registry
SET path = REPLACE(path, 'layer_02_target_context_mapping.csv', 'layer_2_target_context_mapping.csv'),
    updated_at = NOW()
WHERE path LIKE '%layer_02_target_context_mapping.csv%';

UPDATE trading_registry
SET note = REPLACE(note, 'layer_02_target_context_mapping.csv', 'layer_2_target_context_mapping.csv'),
    updated_at = NOW()
WHERE note LIKE '%layer_02_target_context_mapping.csv%';

UPDATE trading_registry
SET payload = 'layer_1_2_market_context_etf_universe.csv;layer_1_2_market_context_relative_strength_combinations.csv;layer_2_target_context_mapping.csv',
    note = 'Shared static files under trading-storage/main/shared use unpadded layer_1_ or layer_2_ filename prefixes for path-level scope clarity while preserving row-level model_layer semantics where applicable.',
    updated_at = NOW()
WHERE key = 'SHARED_LAYER_PREFIXED_STATIC_FILE_NAMES';
