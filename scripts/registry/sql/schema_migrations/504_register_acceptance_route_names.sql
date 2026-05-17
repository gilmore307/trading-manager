-- Align active script/path vocabulary with the first-principles acceptance route.
-- Historical migration filenames and persisted evidence ids remain audit material.

UPDATE trading_registry
SET
  payload = replace(payload, 'build_event_family_remaining_closeout.py', 'build_event_family_remaining_acceptance.py'),
  path = replace(path, 'build_event_family_remaining_closeout.py', 'build_event_family_remaining_acceptance.py'),
  applies_to = replace(applies_to, 'build_event_family_remaining_closeout.py', 'build_event_family_remaining_acceptance.py'),
  note = replace(note, 'build_event_family_remaining_closeout.py', 'build_event_family_remaining_acceptance.py')
WHERE payload LIKE '%build_event_family_remaining_closeout.py%'
   OR path LIKE '%build_event_family_remaining_closeout.py%'
   OR applies_to LIKE '%build_event_family_remaining_closeout.py%'
   OR note LIKE '%build_event_family_remaining_closeout.py%';

UPDATE trading_registry
SET
  payload = replace(payload, 'event_family_remaining_closeout', 'event_family_remaining_acceptance'),
  path = replace(path, 'event_family_remaining_closeout', 'event_family_remaining_acceptance'),
  applies_to = replace(applies_to, 'event_family_remaining_closeout', 'event_family_remaining_acceptance'),
  note = replace(
    replace(
      replace(note, 'remaining event-family closeout artifact', 'remaining event-family acceptance artifact'),
      'event-family closeout', 'event-family acceptance'
    ),
    'closeout artifact', 'acceptance artifact'
  )
WHERE payload LIKE '%event_family_remaining_closeout%'
   OR path LIKE '%event_family_remaining_closeout%'
   OR applies_to LIKE '%event_family_remaining_closeout%'
   OR note LIKE '%event-family closeout%'
   OR note LIKE '%closeout artifact%';

UPDATE trading_registry
SET
  payload = replace(payload, 'build_event_model_closeout_report.py', 'build_event_model_acceptance_report.py'),
  path = replace(path, 'build_event_model_closeout_report.py', 'build_event_model_acceptance_report.py'),
  applies_to = replace(applies_to, 'build_event_model_closeout_report.py', 'build_event_model_acceptance_report.py'),
  note = replace(note, 'build_event_model_closeout_report.py', 'build_event_model_acceptance_report.py')
WHERE payload LIKE '%build_event_model_closeout_report.py%'
   OR path LIKE '%build_event_model_closeout_report.py%'
   OR applies_to LIKE '%build_event_model_closeout_report.py%'
   OR note LIKE '%build_event_model_closeout_report.py%';

UPDATE trading_registry
SET
  payload = replace(payload, 'event_model_closeout', 'event_model_acceptance'),
  path = replace(path, 'event_model_closeout', 'event_model_acceptance'),
  applies_to = replace(applies_to, 'event_model_closeout', 'event_model_acceptance'),
  note = replace(
    replace(note, 'event-model closeout report', 'event-model acceptance report'),
    'event-model closeout', 'event-model acceptance'
  )
WHERE payload LIKE '%event_model_closeout%'
   OR path LIKE '%event_model_closeout%'
   OR applies_to LIKE '%event_model_closeout%'
   OR note LIKE '%event-model closeout%';

UPDATE trading_registry
SET
  payload = replace(payload, 'review_layers_03_08_promotion_closeout.py', 'review_layers_03_08_promotion_acceptance.py'),
  path = replace(path, 'review_layers_03_08_promotion_closeout.py', 'review_layers_03_08_promotion_acceptance.py'),
  applies_to = replace(applies_to, 'review_layers_03_08_promotion_closeout.py', 'review_layers_03_08_promotion_acceptance.py'),
  note = replace(note, 'review_layers_03_08_promotion_closeout.py', 'review_layers_03_08_promotion_acceptance.py')
WHERE payload LIKE '%review_layers_03_08_promotion_closeout.py%'
   OR path LIKE '%review_layers_03_08_promotion_closeout.py%'
   OR applies_to LIKE '%review_layers_03_08_promotion_closeout.py%'
   OR note LIKE '%review_layers_03_08_promotion_closeout.py%';

UPDATE trading_registry
SET
  payload = replace(payload, 'file_lifecycle_closeout', 'file_lifecycle_acceptance'),
  path = replace(path, 'file_lifecycle_closeout', 'file_lifecycle_acceptance'),
  applies_to = replace(applies_to, 'file_lifecycle_closeout', 'file_lifecycle_acceptance'),
  note = replace(
    replace(note, 'one-pass file-lifecycle closeout', 'one-pass file-lifecycle acceptance'),
    'file-lifecycle closeout', 'file-lifecycle acceptance'
  )
WHERE payload LIKE '%file_lifecycle_closeout%'
   OR path LIKE '%file_lifecycle_closeout%'
   OR applies_to LIKE '%file_lifecycle_closeout%'
   OR note LIKE '%file-lifecycle closeout%'
   OR note LIKE '%one-pass file-lifecycle closeout%';

UPDATE trading_registry
SET
  payload = replace(payload, 'run_file_lifecycle_closeout.py', 'run_file_lifecycle_acceptance.py'),
  path = replace(path, 'run_file_lifecycle_closeout.py', 'run_file_lifecycle_acceptance.py'),
  applies_to = replace(applies_to, 'run_file_lifecycle_closeout.py', 'run_file_lifecycle_acceptance.py'),
  note = replace(note, 'run_file_lifecycle_closeout.py', 'run_file_lifecycle_acceptance.py')
WHERE payload LIKE '%run_file_lifecycle_closeout.py%'
   OR path LIKE '%run_file_lifecycle_closeout.py%'
   OR applies_to LIKE '%run_file_lifecycle_closeout.py%'
   OR note LIKE '%run_file_lifecycle_closeout.py%';
