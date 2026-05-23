-- Rename the Layer 1/2 ETF universe grain field now that source acquisition
-- downloads canonical 1-minute bars and downstream feature_generation owns
-- frame derivation.

UPDATE trading_registry
SET key = 'FEATURE_GRAIN',
    payload = 'feature_grain',
    note = 'Intended downstream observation/feature granularity for this ETF, e.g. 1m, 30m, or 1d. It is not the provider download grain for source_01_market_regime; that source downloads canonical 1Min bars and feature_generation derives downstream frames locally.',
    applies_to = 'market_regime_etf_universe;source_01_market_regime;feature_01_market_regime;feature_02_sector_context;one_minute_source_bars',
    updated_at = CURRENT_TIMESTAMP
WHERE id = 'fld_MEU004';

UPDATE trading_registry
SET note = 'Shared curated ETF universe for Layer 1 market-state instruments and Layer 2 sector/industry/theme observation instruments. The model_layer column is the authoritative Layer 1/Layer 2 scope discriminator; universe_type remains descriptive row classification. feature_grain is the intended downstream observation/feature grain; source acquisition downloads canonical 1Min bars.',
    updated_at = CURRENT_TIMESTAMP
WHERE key = 'MARKET_REGIME_ETF_UNIVERSE_SHARED_CSV';
