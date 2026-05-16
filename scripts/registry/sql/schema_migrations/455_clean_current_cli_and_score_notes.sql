-- Align current CLI command payloads and remove stale post-migration score-note
-- language from current registry rows. Historical migration files are not edited.

UPDATE trading_registry
SET payload = 'trading-data-source-08-event-risk-governor',
    updated_at = NOW()
WHERE key = 'SOURCE_08_EVENT_RISK_GOVERNOR_RUN'
  AND payload = 'trading-data-source-04-event-overlay';

UPDATE trading_registry
SET payload = 'trading-data-feature-08-event-risk-governor',
    updated_at = NOW()
WHERE key = 'FEATURE_08_EVENT_RISK_GOVERNOR_GENERATE'
  AND payload = 'trading-data-feature-04-event-overlay';

UPDATE trading_registry
SET payload = 'trading-data-feature-07-option-expression',
    updated_at = NOW()
WHERE key = 'FEATURE_07_OPTION_EXPRESSION_GENERATE'
  AND payload = 'trading-data-feature-08-option-expression';

UPDATE trading_registry
SET note = replace(note, ' Physical value name remains current 4_* until dedicated migration.', ''),
    updated_at = NOW()
WHERE note LIKE '%Physical value name remains current 4_* until dedicated migration.%';

UPDATE trading_registry
SET note = replace(note, ' Physical value name remains current 7_* until dedicated migration.', ''),
    updated_at = NOW()
WHERE note LIKE '%Physical value name remains current 7_* until dedicated migration.%';

UPDATE trading_registry
SET note = replace(note, ' Current value name uses the Layer 5 prefix.', ''),
    updated_at = NOW()
WHERE note LIKE '%Current value name uses the Layer 5 prefix.%';

UPDATE trading_registry
SET note = replace(note, ' Current value name uses the Layer 6 prefix.', ''),
    updated_at = NOW()
WHERE note LIKE '%Current value name uses the Layer 6 prefix.%';

UPDATE trading_registry
SET note = replace(note, 'Layer 6 point-in-time current position state input.', 'Layer 5 point-in-time current position state input.'),
    updated_at = NOW()
WHERE key = 'CURRENT_POSITION_STATE';

UPDATE trading_registry
SET note = replace(note, 'Layer 7 point-in-time current direct-underlying position state input.', 'Layer 6 point-in-time current direct-underlying position state input.'),
    updated_at = NOW()
WHERE key = 'CURRENT_UNDERLYING_POSITION_STATE';
