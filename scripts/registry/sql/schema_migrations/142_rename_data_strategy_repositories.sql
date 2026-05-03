-- Rename the component repository boundary from broad data/strategy names
-- to source/derived dataset-layer names.
--
-- trading-source owns external/source-backed observed data. trading-derived
-- owns internally generated labels, samples, signals, candidates, oracle
-- outcomes, backtest/evaluation outputs, and related derived datasets.

UPDATE trading_registry
SET key = replace(replace(key, 'TRADING_DATA', 'TRADING_SOURCE'), 'TRADING_STRATEGY', 'TRADING_DERIVED'),
    payload = replace(
      replace(
        replace(
          replace(payload, 'trading-data', 'trading-source'),
          'trading-strategy', 'trading-derived'
        ),
        'trading_data', 'trading_source'
      ),
      'trading_strategy', 'trading_derived'
    ),
    path = replace(
      replace(
        replace(
          replace(path, 'trading-data', 'trading-source'),
          'trading-strategy', 'trading-derived'
        ),
        'trading_data', 'trading_source'
      ),
      'trading_strategy', 'trading_derived'
    ),
    applies_to = replace(
      replace(
        replace(
          replace(applies_to, 'trading-data', 'trading-source'),
          'trading-strategy', 'trading-derived'
        ),
        'trading_data', 'trading_source'
      ),
      'trading_strategy', 'trading_derived'
    ),
    note = replace(
      replace(
        replace(
          replace(
            replace(
              replace(note, 'TRADING_DATA', 'TRADING_SOURCE'),
              'TRADING_STRATEGY', 'TRADING_DERIVED'
            ),
            'trading-data', 'trading-source'
          ),
          'trading-strategy', 'trading-derived'
        ),
        'trading_data', 'trading_source'
      ),
      'trading_strategy', 'trading_derived'
    )
WHERE key LIKE '%TRADING_DATA%'
   OR key LIKE '%TRADING_STRATEGY%'
   OR payload LIKE '%trading-data%'
   OR payload LIKE '%trading-strategy%'
   OR payload LIKE '%trading_data%'
   OR payload LIKE '%trading_strategy%'
   OR path LIKE '%trading-data%'
   OR path LIKE '%trading-strategy%'
   OR path LIKE '%trading_data%'
   OR path LIKE '%trading_strategy%'
   OR applies_to LIKE '%trading-data%'
   OR applies_to LIKE '%trading-strategy%'
   OR applies_to LIKE '%trading_data%'
   OR applies_to LIKE '%trading_strategy%'
   OR note LIKE '%TRADING_DATA%'
   OR note LIKE '%TRADING_STRATEGY%'
   OR note LIKE '%trading-data%'
   OR note LIKE '%trading-strategy%'
   OR note LIKE '%trading_data%'
   OR note LIKE '%trading_strategy%';

UPDATE trading_registry
SET note = 'canonical repository entry for the trading external/source-backed observed-data component; remote: https://github.com/gilmore307/trading-source.git'
WHERE id = 'rep_QFYSFJG9';

UPDATE trading_registry
SET note = 'canonical repository entry for the trading internally generated/derived-data component; remote: https://github.com/gilmore307/trading-derived.git'
WHERE id = 'rep_FM2IMQZA';
