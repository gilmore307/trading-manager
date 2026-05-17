-- Rename active registry keys and route labels from closeout to acceptance.
-- Historical migration names and durable receipt identifiers remain audit evidence.

UPDATE trading_registry
SET key = 'MODEL_PROMOTION_ACCEPTANCE_BLOCKERS'
WHERE key = 'MODEL_PROMOTION_CLOSEOUT_BLOCKERS';

UPDATE trading_registry
SET key = 'MODEL_PROMOTION_ACCEPTANCE_DECISION_RECEIPTS',
    applies_to = replace(applies_to, 'promotion_closeout', 'promotion_acceptance')
WHERE key = 'MODEL_PROMOTION_CLOSEOUT_DECISION_RECEIPTS';

UPDATE trading_registry
SET key = 'TRADING_DATA_STACK_ACCEPTANCE_STATUS',
    note = replace(
      replace(note, 'Accepted trading-data closeout', 'Accepted trading-data acceptance'),
      'closeout status', 'acceptance status'
    )
WHERE key = 'TRADING_DATA_STACK_CLOSEOUT_STATUS';

UPDATE trading_registry
SET key = 'TRADING_MANAGER_CONTROL_PLANE_ACCEPTANCE_STATUS',
    applies_to = replace(applies_to, 'closeout', 'acceptance'),
    note = replace(note, 'control-plane closeout status', 'control-plane acceptance status')
WHERE key = 'TRADING_MANAGER_CONTROL_PLANE_CLOSEOUT_STATUS';

UPDATE trading_registry
SET key = 'MODEL_09_EVENT_FAMILY_REMAINING_ACCEPTANCE_BUILD',
    note = replace(
      replace(note, 'remaining event-family closeout artifact', 'remaining event-family acceptance artifact'),
      'event-family closeout artifact', 'event-family acceptance artifact'
    )
WHERE key = 'MODEL_09_EVENT_FAMILY_REMAINING_CLOSEOUT_BUILD';

UPDATE trading_registry
SET key = 'MODEL_09_EVENT_RISK_GOVERNOR_ACCEPTANCE_REPORT_BUILD',
    note = replace(note, 'event-model closeout report', 'event-model acceptance report')
WHERE key = 'MODEL_09_EVENT_RISK_GOVERNOR_CLOSEOUT_REPORT_BUILD';

UPDATE trading_registry
SET key = 'REVIEW_LAYERS_03_08_PROMOTION_ACCEPTANCE',
    note = replace(note, 'promotion-closeout entrypoint', 'promotion-acceptance entrypoint')
WHERE key = 'REVIEW_LAYERS_03_08_PROMOTION_CLOSEOUT';

UPDATE trading_registry
SET key = 'STORAGE_FILE_LIFECYCLE_ACCEPTANCE_RUN',
    note = replace(note, 'file-lifecycle closeout', 'file-lifecycle acceptance')
WHERE key = 'STORAGE_FILE_LIFECYCLE_CLOSEOUT_RUN';

UPDATE trading_registry
SET note = replace(note, 'closeout/evaluation/review', 'acceptance/evaluation/review')
WHERE key = 'MANAGER_PLAN_EVENT_MODEL_REGENERATION';
