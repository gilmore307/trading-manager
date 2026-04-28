-- Refine reviewed field-category assignments where lexical fallback was too broad.

UPDATE trading_registry
SET field_category = 'temporal'
WHERE kind = 'field'
  AND key IN (
    'EVENT_FACTOR_AS_OF_ET',
    'WINDOW_START_ET',
    'WINDOW_END_ET'
  );

UPDATE trading_registry
SET field_category = 'numeric_measure'
WHERE kind = 'field'
  AND key IN (
    'OPTION_EVENT_STANDARD_MIN_VOLUME_PERCENTILE_20D_SAME_TIME',
    'VOLUME_PERCENTILE_20D_SAME_TIME',
    'VOLUME_VS_PRIOR_WINDOW_RATIO',
    'VOLUME_ZSCORE'
  );

UPDATE trading_registry
SET field_category = 'classification'
WHERE kind = 'field'
  AND key IN (
    'GDELT_IMPACT_SCOPE_HINT',
    'OPTION_EVENT_TRIGGER_IV_HIGH_CROSS_SECTION',
    'OPTION_EVENT_TRIGGER_OPENING_ACTIVITY',
    'OPTION_EVENT_TRIGGER_TRADE_AT_ASK',
    'SOURCE'
  );
