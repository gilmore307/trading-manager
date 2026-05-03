UPDATE trading_registry
SET note = 'Curated Layer 1 V1 relative-strength combination table for MarketRegimeModel derived features. Rows define numerator/denominator ETF pairs, source bar grains, feature_bar_grain, combination_type, and interpretation; the file scope already fixes the feature family as relative strength.',
    updated_at = CURRENT_TIMESTAMP
WHERE key = 'MARKET_REGIME_RELATIVE_STRENGTH_COMBINATIONS_SHARED_CSV';

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
    (
        'fld_MRRS001',
        'identity_field',
        'COMBINATION_ID',
        'field_name',
        'combination_id',
        'trading-storage/main/shared/market_regime_relative_strength_combinations.csv',
        'market_regime_relative_strength_combinations;trading-derived;market_regime_model',
        'sync_artifact',
        'Stable row identifier for a reviewed relative-strength ETF combination.'
    ),
    (
        'fld_MRRS002',
        'classification_field',
        'COMBINATION_TYPE',
        'field_name',
        'combination_type',
        'trading-storage/main/shared/market_regime_relative_strength_combinations.csv',
        'market_regime_relative_strength_combinations;trading-derived;market_regime_model',
        'sync_artifact',
        'Classification axis for the reviewed combination role, such as primary, sector_rotation, or daily_context.'
    ),
    (
        'fld_MRRS003',
        'identity_field',
        'NUMERATOR_SYMBOL',
        'field_name',
        'numerator_symbol',
        'trading-storage/main/shared/market_regime_relative_strength_combinations.csv',
        'market_regime_relative_strength_combinations;trading-derived;market_regime_model',
        'sync_artifact',
        'ETF symbol used as the numerator of a relative-strength combination.'
    ),
    (
        'fld_MRRS004',
        'identity_field',
        'DENOMINATOR_SYMBOL',
        'field_name',
        'denominator_symbol',
        'trading-storage/main/shared/market_regime_relative_strength_combinations.csv',
        'market_regime_relative_strength_combinations;trading-derived;market_regime_model',
        'sync_artifact',
        'ETF symbol used as the denominator of a relative-strength combination.'
    ),
    (
        'fld_MRRS005',
        'field',
        'NUMERATOR_BAR_GRAIN',
        'field_name',
        'numerator_bar_grain',
        'trading-storage/main/shared/market_regime_relative_strength_combinations.csv',
        'market_regime_relative_strength_combinations;trading-derived;market_regime_model',
        'sync_artifact',
        'Source acquisition/detail bar grain for the numerator ETF symbol.'
    ),
    (
        'fld_MRRS006',
        'field',
        'DENOMINATOR_BAR_GRAIN',
        'field_name',
        'denominator_bar_grain',
        'trading-storage/main/shared/market_regime_relative_strength_combinations.csv',
        'market_regime_relative_strength_combinations;trading-derived;market_regime_model',
        'sync_artifact',
        'Source acquisition/detail bar grain for the denominator ETF symbol.'
    ),
    (
        'fld_MRRS007',
        'field',
        'FEATURE_BAR_GRAIN',
        'field_name',
        'feature_bar_grain',
        'trading-storage/main/shared/market_regime_relative_strength_combinations.csv',
        'market_regime_relative_strength_combinations;trading-derived;market_regime_model',
        'sync_artifact',
        'Derived feature bar grain for a relative-strength combination row.'
    ),
    (
        'fld_MRRS008',
        'text_field',
        'INTERPRETATION',
        'field_name',
        'interpretation',
        'trading-storage/main/shared/market_regime_relative_strength_combinations.csv',
        'market_regime_relative_strength_combinations;trading-derived;market_regime_model',
        'sync_artifact',
        'Human-readable interpretation of what the relative-strength combination measures.'
    )
ON CONFLICT (id) DO UPDATE SET
    kind = excluded.kind,
    key = excluded.key,
    payload_format = excluded.payload_format,
    payload = excluded.payload,
    path = excluded.path,
    applies_to = excluded.applies_to,
    artifact_sync_policy = excluded.artifact_sync_policy,
    note = excluded.note,
    updated_at = CURRENT_TIMESTAMP;
