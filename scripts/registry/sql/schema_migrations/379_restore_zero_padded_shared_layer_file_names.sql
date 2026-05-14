-- Restore zero-padded layer filename prefixes for consistency with established layer numbering.

UPDATE trading_registry
SET payload = REPLACE(payload, 'layer_1_2_market_context_etf_universe.csv', 'layer_01_02_market_context_etf_universe.csv'),
    updated_at = NOW()
WHERE payload LIKE '%layer_1_2_market_context_etf_universe.csv%';

UPDATE trading_registry
SET path = REPLACE(path, 'layer_1_2_market_context_etf_universe.csv', 'layer_01_02_market_context_etf_universe.csv'),
    updated_at = NOW()
WHERE path LIKE '%layer_1_2_market_context_etf_universe.csv%';

UPDATE trading_registry
SET note = REPLACE(note, 'layer_1_2_market_context_etf_universe.csv', 'layer_01_02_market_context_etf_universe.csv'),
    updated_at = NOW()
WHERE note LIKE '%layer_1_2_market_context_etf_universe.csv%';

UPDATE trading_registry
SET payload = REPLACE(payload, 'layer_1_2_market_context_relative_strength_combinations.csv', 'layer_01_02_market_context_relative_strength_combinations.csv'),
    updated_at = NOW()
WHERE payload LIKE '%layer_1_2_market_context_relative_strength_combinations.csv%';

UPDATE trading_registry
SET path = REPLACE(path, 'layer_1_2_market_context_relative_strength_combinations.csv', 'layer_01_02_market_context_relative_strength_combinations.csv'),
    updated_at = NOW()
WHERE path LIKE '%layer_1_2_market_context_relative_strength_combinations.csv%';

UPDATE trading_registry
SET note = REPLACE(note, 'layer_1_2_market_context_relative_strength_combinations.csv', 'layer_01_02_market_context_relative_strength_combinations.csv'),
    updated_at = NOW()
WHERE note LIKE '%layer_1_2_market_context_relative_strength_combinations.csv%';

UPDATE trading_registry
SET payload = REPLACE(payload, 'layer_2_target_context_mapping.csv', 'layer_02_target_context_mapping.csv'),
    updated_at = NOW()
WHERE payload LIKE '%layer_2_target_context_mapping.csv%';

UPDATE trading_registry
SET path = REPLACE(path, 'layer_2_target_context_mapping.csv', 'layer_02_target_context_mapping.csv'),
    updated_at = NOW()
WHERE path LIKE '%layer_2_target_context_mapping.csv%';

UPDATE trading_registry
SET note = REPLACE(note, 'layer_2_target_context_mapping.csv', 'layer_02_target_context_mapping.csv'),
    updated_at = NOW()
WHERE note LIKE '%layer_2_target_context_mapping.csv%';

UPDATE trading_registry
SET payload = 'layer_01_02_market_context_etf_universe.csv;layer_01_02_market_context_relative_strength_combinations.csv;layer_02_target_context_mapping.csv',
    note = 'Shared static files under trading-storage/main/shared use zero-padded layer_01_ or layer_02_ filename prefixes for path-level scope clarity while preserving row-level model_layer semantics where applicable.',
    updated_at = NOW()
WHERE key = 'SHARED_LAYER_PREFIXED_STATIC_FILE_NAMES';
