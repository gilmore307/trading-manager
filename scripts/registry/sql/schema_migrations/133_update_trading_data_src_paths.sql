-- Update active trading-data source paths after removing the redundant
-- src/trading_data package directory. Importable packages now live directly
-- under trading-data/src/.

UPDATE trading_registry
SET path = replace(path, 'trading-data/src/trading_data/', 'trading-data/src/'),
    note = CASE
      WHEN note LIKE '%trading-data src packages now live directly under src/%' THEN note
      ELSE note || ' Path updated 2026-04-28: trading-data src packages now live directly under src/ without a redundant trading_data package directory.'
    END
WHERE path LIKE 'trading-data/src/trading_data/%';

UPDATE trading_registry
SET path = replace(path, '/root/projects/trading-data/src/trading_data/', '/root/projects/trading-data/src/'),
    note = CASE
      WHEN note LIKE '%trading-data src packages now live directly under src/%' THEN note
      ELSE note || ' Path updated 2026-04-28: trading-data src packages now live directly under src/ without a redundant trading_data package directory.'
    END
WHERE path LIKE '/root/projects/trading-data/src/trading_data/%';
