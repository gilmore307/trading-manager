-- Rename market ETF universe classification fields to type-style column names.
-- Target engine: PostgreSQL.

UPDATE trading_registry
SET key = 'UNIVERSE_TYPE',
    payload = 'universe_type',
    note = 'classification type for an instrument inside a curated universe, such as market_state_etf or sector_observation_etf'
WHERE id = 'fld_MEU002';

UPDATE trading_registry
SET key = 'EXPOSURE_TYPE',
    payload = 'exposure_type',
    note = 'market/sector/theme exposure classification type such as us_equity_core, sp500_sector, industry_chain, thematic_growth, crypto_beta, commodities, credit, rates_curve, or usd_volatility'
WHERE id = 'fld_MEU003';
