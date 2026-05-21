-- Finish active registry cleanup after the 10-layer physical cutover.

UPDATE trading_registry
SET key = replace(key, 'LAYER_08_OPTION_EXPRESSION', 'LAYER_09_OPTION_EXPRESSION'),
    payload = replace(payload, 'layer_08_option_expression', 'layer_09_option_expression'),
    applies_to = replace(applies_to, 'layer_08_option_expression', 'layer_09_option_expression'),
    note = replace(note, 'layer_08_option_expression', 'layer_09_option_expression'),
    updated_at = NOW()
WHERE key LIKE '%LAYER_08_OPTION_EXPRESSION%'
   OR payload LIKE '%layer_08_option_expression%'
   OR applies_to LIKE '%layer_08_option_expression%'
   OR note LIKE '%layer_08_option_expression%';

UPDATE trading_registry
SET key = replace(key, 'LAYER_08_OPTION', 'LAYER_09_OPTION'),
    updated_at = NOW()
WHERE key LIKE '%LAYER_08_OPTION%';

UPDATE trading_registry
SET path = replace(path, 'trading-model/docs/18_layer_09_event_risk_governor.md', 'trading-model/docs/19_layer_10_event_risk_governor.md'),
    updated_at = NOW()
WHERE path LIKE '%trading-model/docs/18_layer_09_event_risk_governor.md%';

UPDATE trading_registry
SET payload = replace(payload, '9_event_', '10_event_'),
    updated_at = NOW()
WHERE payload LIKE '%9_event_%'
  AND (
    applies_to LIKE '%event_context_vector%'
    OR applies_to LIKE '%event_risk_governor%'
    OR key LIKE '%EVENT_%'
  );

UPDATE trading_registry
SET note = replace(replace(replace(replace(replace(replace(replace(note,
        'Layer 9 event-governor', 'Layer 10 event-governor'),
        'Layer 9 event-risk', 'Layer 10 event-risk'),
        'Layer 9 point-in-time event-context', 'Layer 10 point-in-time event-context'),
        'Accepted Layer 9 event-risk governor', 'Accepted Layer 10 event-risk governor'),
        'bounded Layer 9 event-risk', 'bounded Layer 10 event-risk'),
        'Layer 8 option-expression', 'Layer 9 option-expression'),
        'Layer 7 thesis', 'Layer 8 thesis'),
    updated_at = NOW()
WHERE note LIKE '%Layer 9 event-governor%'
   OR note LIKE '%Layer 9 event-risk%'
   OR note LIKE '%Layer 9 point-in-time event-context%'
   OR note LIKE '%Accepted Layer 9 event-risk governor%'
   OR note LIKE '%bounded Layer 9 event-risk%'
   OR note LIKE '%Layer 8 option-expression%'
   OR note LIKE '%Layer 7 thesis%';

UPDATE trading_registry
SET note = replace(replace(replace(note,
        'Current 8_*', 'Current 9_*'),
        'current 8_*', 'current 9_*'),
        'Layer 8 gate', 'Layer 9 gate'),
    updated_at = NOW()
WHERE note LIKE '%Current 8_*%'
   OR note LIKE '%current 8_*%'
   OR note LIKE '%Layer 8 gate%';

UPDATE trading_registry
SET applies_to = replace(applies_to, 'layer_09_event_risk_governor', 'layer_10_event_risk_governor'),
    note = replace(note, 'layer_09_event_risk_governor', 'layer_10_event_risk_governor'),
    updated_at = NOW()
WHERE applies_to LIKE '%layer_09_event_risk_governor%'
   OR note LIKE '%layer_09_event_risk_governor%';

UPDATE trading_registry
SET applies_to = replace(applies_to, 'model_09_event_risk_governor', 'model_10_event_risk_governor'),
    note = replace(note, 'model_09_event_risk_governor', 'model_10_event_risk_governor'),
    updated_at = NOW()
WHERE applies_to LIKE '%model_09_event_risk_governor%'
   OR note LIKE '%model_09_event_risk_governor%';

