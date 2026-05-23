-- Record the accepted market-context source policy: download one canonical
-- 1-minute bar stream and derive downstream frames during feature generation.

UPDATE trading_registry
SET note = 'Layer 1/2 market-context ETF bar source. Downloads only canonical 1Min raw Alpaca bars into trading_data.source_01_market_regime; downstream feature_generation derives 1min, 5min, 30min, and 1d evidence locally. Provider-native 30Min/1Day rows must not be mixed into this source table.',
    applies_to = 'trading-data;trading-model;market_regime_model;sector_context_model;feature_01_market_regime;feature_02_sector_context;one_minute_source_bars',
    updated_at = CURRENT_TIMESTAMP
WHERE key = 'SOURCE_01_MARKET_REGIME';

UPDATE trading_registry
SET note = 'Layer 1 MarketRegimeModel deterministic feature-output boundary. Each row is one point-in-time market-regime feature snapshot keyed by snapshot_time, input_frame, prediction_horizon, and market_universe_ref; generated feature values are stored as model-local keys in feature_payload_json JSONB to avoid PostgreSQL row-size limits. Feature generation consumes canonical 1Min source_01_market_regime rows and locally derives accepted frame surfaces; future return, volatility, drawdown, transition, and tradability outcomes are labels/evaluation evidence only, not same-row construction input.',
    applies_to = 'trading-data;trading-model;market_regime_model;source_01_market_regime;input_frame;prediction_horizon;market_universe_ref;one_minute_source_bars',
    updated_at = CURRENT_TIMESTAMP
WHERE key = 'FEATURE_01_MARKET_REGIME';

UPDATE trading_registry
SET note = 'Layer 2 deterministic feature surface for SectorContextModel sector/industry relative strength, normalized trend, volatility-ratio, correlation, breadth, and dispersion evidence. Feature generation consumes canonical 1Min source_01_market_regime rows and locally derives 30-minute and daily sector-context evidence; feature_bar_grain remains the reviewed feature-grain contract, not a provider download contract.',
    applies_to = 'trading-data;trading-model;sector_context_model;source_01_market_regime;one_minute_source_bars',
    updated_at = CURRENT_TIMESTAMP
WHERE key = 'FEATURE_02_SECTOR_CONTEXT';

UPDATE trading_registry
SET note = 'Intended downstream observation/feature granularity for this ETF, e.g. 1m, 30m, or 1d. It is not the provider download grain for source_01_market_regime; that source downloads canonical 1Min bars and feature_generation derives downstream frames locally.',
    applies_to = 'market_regime_etf_universe;source_01_market_regime;feature_01_market_regime;feature_02_sector_context;one_minute_source_bars',
    updated_at = CURRENT_TIMESTAMP
WHERE key = 'BAR_GRAIN';

UPDATE trading_registry
SET note = 'Reviewed downstream feature bar grain for a relative-strength combination row. It controls local feature derivation from canonical 1Min source bars, not provider-native multi-frame download requests.',
    applies_to = 'market_regime_relative_strength_combinations;trading-data;market_regime_model;sector_context_model;feature_01_market_regime;feature_02_sector_context;one_minute_source_bars',
    updated_at = CURRENT_TIMESTAMP
WHERE key = 'FEATURE_BAR_GRAIN';

UPDATE trading_registry
SET note = 'Numerator ETF source-observation cue retained for reviewed relative-strength metadata. Market-context acquisition still downloads canonical 1Min bars; downstream feature_generation derives this row’s feature grain locally.',
    updated_at = CURRENT_TIMESTAMP
WHERE key = 'NUMERATOR_BAR_GRAIN';

UPDATE trading_registry
SET note = 'Denominator ETF source-observation cue retained for reviewed relative-strength metadata. Market-context acquisition still downloads canonical 1Min bars; downstream feature_generation derives this row’s feature grain locally.',
    updated_at = CURRENT_TIMESTAMP
WHERE key = 'DENOMINATOR_BAR_GRAIN';

UPDATE trading_registry
SET note = 'Stable package CLI entrypoint for generating Layer 1 MarketRegimeModel deterministic feature rows from accepted canonical 1Min source_01_market_regime evidence. The importable implementation lives under src/data_feature/feature_01_market_regime.',
    applies_to = 'trading-data;market_regime_model;feature_01_market_regime;source_01_market_regime;one_minute_source_bars',
    updated_at = CURRENT_TIMESTAMP
WHERE key = 'FEATURE_01_MARKET_REGIME_GENERATE';

UPDATE trading_registry
SET note = 'Stable package CLI entrypoint for generating Layer 2 SectorContextModel deterministic feature rows from accepted canonical 1Min source_01_market_regime evidence. The importable implementation lives under src/data_feature/feature_02_sector_context.',
    applies_to = 'trading-data;sector_context_model;feature_02_sector_context;source_01_market_regime;one_minute_source_bars',
    updated_at = CURRENT_TIMESTAMP
WHERE key = 'FEATURE_02_SECTOR_CONTEXT_GENERATE';
