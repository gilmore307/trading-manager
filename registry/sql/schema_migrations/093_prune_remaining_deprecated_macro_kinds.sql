-- Remove remaining deprecated macro_data-era data kinds and orphaned transient
-- macro_release fields. The active final event shape is macro_release_event.

DELETE FROM trading_registry
WHERE kind = 'data_kind'
  AND key IN (
    'MACRO_ALFRED_VINTAGE',
    'MACRO_BEA_NIPA',
    'MACRO_BLS_CPI',
    'MACRO_FRED_NATIVE',
    'MACRO_RELEASE',
    'MACRO_TREASURY_DTS'
  );

DELETE FROM trading_registry
WHERE kind = 'field'
  AND key IN (
    'MACRO_RELEASE_TIME',
    'MACRO_EFFECTIVE_UNTIL'
  );
