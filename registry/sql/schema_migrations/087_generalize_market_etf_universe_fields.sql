-- Use generic shared field keys for market_etf_universe where the column names are reusable.
-- Target engine: PostgreSQL.

DELETE FROM trading_registry
WHERE id IN ('fld_MEU001', 'fld_MEU006');

UPDATE trading_registry
SET applies_to = CASE
      WHEN applies_to LIKE '%market_etf_universe%' THEN applies_to
      ELSE applies_to || ';market_etf_universe'
    END,
    note = 'generic model-facing instrument symbol field shared by market outputs and curated instrument universes'
WHERE id = 'fld_MKT001';

UPDATE trading_registry
SET key = 'ISSUER',
    applies_to = CASE
      WHEN applies_to LIKE '%market_etf_universe%' THEN applies_to
      ELSE applies_to || ';market_etf_universe'
    END,
    note = 'issuer/source/sponsor display name shared by ETF holdings and curated instrument universes'
WHERE id = 'fld_ETFH002';

UPDATE trading_registry
SET key = 'UNIVERSE_ROLE',
    note = 'role of an instrument inside a curated universe, such as market_state_etf or sector_observation_etf'
WHERE id = 'fld_MEU002';

UPDATE trading_registry
SET key = 'EXPOSURE_CATEGORY',
    note = 'market/sector/theme exposure category such as us_equity_core, sp500_sector, industry_chain, thematic_growth, crypto_beta, commodities, credit, rates_curve, or usd_volatility'
WHERE id = 'fld_MEU003';

UPDATE trading_registry
SET key = 'BAR_GRAIN',
    note = 'intended observation bar granularity, e.g. 1m, 30m, or 1d'
WHERE id = 'fld_MEU004';

UPDATE trading_registry
SET key = 'FUND_NAME',
    note = 'human-readable fund name'
WHERE id = 'fld_MEU005';
