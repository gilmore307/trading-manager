-- Remove field-like registry rows that only described obsolete preview/template
-- files. Keep only fields used by accepted final SQL model-input tables or
-- still-valid shared/registry/task artifacts, and strip template applies_to
-- pollution from retained rows.

UPDATE trading_registry
SET applies_to = CASE WHEN applies_to LIKE '%option_expression_contract_snapshot%'
                      THEN applies_to
                      ELSE applies_to || ';option_expression_contract_snapshot'
                 END,
    updated_at = CURRENT_TIMESTAMP
WHERE key IN (
  'QUOTE_BID', 'QUOTE_ASK', 'QUOTE_MID', 'QUOTE_SPREAD', 'QUOTE_SPREAD_PCT',
  'QUOTE_BID_SIZE', 'QUOTE_ASK_SIZE', 'IMPLIED_VOL', 'IV_ERROR',
  'GREEK_DELTA', 'GREEK_THETA', 'GREEK_VEGA', 'GREEK_RHO',
  'GREEK_EPSILON', 'GREEK_LAMBDA', 'UNDERLYING_PRICE',
  'UNDERLYING_TIMESTAMP', 'OPTION_DAYS_TO_EXPIRATION'
);

DELETE FROM trading_registry
WHERE kind IN ('field', 'identity_field', 'path_field', 'temporal_field', 'classification_field', 'text_field', 'parameter_field')
  AND path LIKE 'trading-data/storage/templates/data_kinds/%'
  AND NOT (
    applies_to LIKE '%market_regime_etf_bar%'
    OR applies_to LIKE '%security_selection_us_equity_etf_holding%'
    OR applies_to LIKE '%strategy_selection_symbol_bar_liquidity%'
    OR applies_to LIKE '%option_expression_contract_snapshot%'
    OR applies_to LIKE '%position_execution_option_contract_timeseries%'
    OR applies_to LIKE '%event_overlay_event%'
    OR applies_to LIKE '%market_etf_universe%'
    OR applies_to LIKE '%trading_registry%'
    OR applies_to LIKE '%data_task_key%'
    OR applies_to LIKE '%data_task_completion_receipt%'
    OR applies_to LIKE '%data_task_completion_receipt_run%'
    OR applies_to LIKE '%execution_key_slots%'
    OR applies_to LIKE '%completion_receipt_slots%'
    OR applies_to LIKE '%acceptance_receipt_slots%'
    OR applies_to LIKE '%maintenance_output_slots%'
  );

UPDATE trading_registry
SET applies_to = cleaned.applies_to,
    path = NULL,
    updated_at = CURRENT_TIMESTAMP
FROM (
  SELECT id, string_agg(part, ';' ORDER BY ord) AS applies_to
  FROM trading_registry,
       unnest(string_to_array(applies_to, ';')) WITH ORDINALITY AS parts(part, ord)
  WHERE kind IN ('field', 'identity_field', 'path_field', 'temporal_field', 'classification_field', 'text_field', 'parameter_field')
    AND path LIKE 'trading-data/storage/templates/data_kinds/%'
    AND part NOT LIKE '%_template'
    AND part <> 'option_template'
    AND part <> 'data_kind_template'
  GROUP BY id
) AS cleaned
WHERE trading_registry.id = cleaned.id;
