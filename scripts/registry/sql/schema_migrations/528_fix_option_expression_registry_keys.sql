-- Finish active OptionExpression registry key cleanup after Layer 8 adoption.

UPDATE trading_registry
SET
  key = REPLACE(key, 'MODEL_09_OPTION_EXPRESSION', 'MODEL_08_OPTION_EXPRESSION'),
  note = REPLACE(note, 'Layer 7 OptionExpressionModel', 'Layer 8 OptionExpressionModel'),
  updated_at = NOW()
WHERE key LIKE '%MODEL_09_OPTION_EXPRESSION%'
   OR note LIKE '%Layer 7 OptionExpressionModel%';
