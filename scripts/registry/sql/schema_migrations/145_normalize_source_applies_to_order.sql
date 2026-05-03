-- Normalize manager-facing source scopes in applies_to to the same number-first
-- shape used by payloads and package paths: NN_source_<layer>.

UPDATE trading_registry
SET applies_to = replace(
                 replace(
                 replace(
                 replace(
                 replace(
                 replace(applies_to,
                   'source_01_market_regime', '01_source_market_regime'),
                   'source_02_security_selection', '02_source_security_selection'),
                   'source_03_strategy_selection', '03_source_strategy_selection'),
                   'source_05_option_expression', '05_source_option_expression'),
                   'source_06_position_execution', '06_source_position_execution'),
                   'source_07_event_overlay', '07_source_event_overlay')
WHERE applies_to LIKE '%source_01_market_regime%'
   OR applies_to LIKE '%source_02_security_selection%'
   OR applies_to LIKE '%source_03_strategy_selection%'
   OR applies_to LIKE '%source_05_option_expression%'
   OR applies_to LIKE '%source_06_position_execution%'
   OR applies_to LIKE '%source_07_event_overlay%';
