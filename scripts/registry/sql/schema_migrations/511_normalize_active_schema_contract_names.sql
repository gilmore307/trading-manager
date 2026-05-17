-- Normalize active schema and lock contract references to stable semantic names.
-- Version history remains in migrations; checked-in schema filenames/titles and active
-- registry references use unversioned contract ids.

UPDATE trading_registry
SET payload = replace(replace(replace(replace(replace(replace(replace(replace(payload,
      'manager_request_v1', 'manager_request'),
      'input_binding_v1', 'input_binding'),
      'run_manifest_v1', 'run_manifest'),
      'run_step_v1', 'run_step'),
      'artifact_ref_v1', 'artifact_ref'),
      'ready_signal_v1', 'ready_signal'),
      'scheduler_lock_plan_v1', 'scheduler_lock_plan'),
      'scheduler_lock_v1', 'scheduler_lock'),
    path = replace(replace(replace(replace(replace(replace(replace(replace(path,
      'manager_request_v1.schema.json', 'manager_request.schema.json'),
      'input_binding_v1.schema.json', 'input_binding.schema.json'),
      'run_manifest_v1.schema.json', 'run_manifest.schema.json'),
      'artifact_ref_v1.schema.json', 'artifact_ref.schema.json'),
      'ready_signal_v1.schema.json', 'ready_signal.schema.json'),
      'scheduler_lock_plan_v1', 'scheduler_lock_plan'),
      'scheduler_lock_v1.schema.json', 'scheduler_lock.schema.json'),
      'scheduler_lock_v1', 'scheduler_lock'),
    applies_to = replace(replace(replace(replace(replace(replace(replace(replace(applies_to,
      'manager_request_v1', 'manager_request'),
      'input_binding_v1', 'input_binding'),
      'run_manifest_v1', 'run_manifest'),
      'run_step_v1', 'run_step'),
      'artifact_ref_v1', 'artifact_ref'),
      'ready_signal_v1', 'ready_signal'),
      'scheduler_lock_plan_v1', 'scheduler_lock_plan'),
      'scheduler_lock_v1', 'scheduler_lock'),
    note = replace(replace(replace(replace(replace(replace(replace(replace(note,
      'manager_request_v1', 'manager_request'),
      'input_binding_v1', 'input_binding'),
      'run_manifest_v1', 'run_manifest'),
      'run_step_v1', 'run_step'),
      'artifact_ref_v1', 'artifact_ref'),
      'ready_signal_v1', 'ready_signal'),
      'scheduler_lock_plan_v1', 'scheduler_lock_plan'),
      'scheduler_lock_v1', 'scheduler_lock'),
    updated_at = NOW()
WHERE payload LIKE '%manager_request_v1%'
   OR payload LIKE '%input_binding_v1%'
   OR payload LIKE '%run_manifest_v1%'
   OR payload LIKE '%run_step_v1%'
   OR payload LIKE '%artifact_ref_v1%'
   OR payload LIKE '%ready_signal_v1%'
   OR payload LIKE '%scheduler_lock_v1%'
   OR payload LIKE '%scheduler_lock_plan_v1%'
   OR path LIKE '%manager_request_v1.schema.json%'
   OR path LIKE '%input_binding_v1.schema.json%'
   OR path LIKE '%run_manifest_v1.schema.json%'
   OR path LIKE '%artifact_ref_v1.schema.json%'
   OR path LIKE '%ready_signal_v1.schema.json%'
   OR path LIKE '%scheduler_lock_v1%'
   OR path LIKE '%scheduler_lock_plan_v1%'
   OR applies_to LIKE '%manager_request_v1%'
   OR applies_to LIKE '%input_binding_v1%'
   OR applies_to LIKE '%run_manifest_v1%'
   OR applies_to LIKE '%run_step_v1%'
   OR applies_to LIKE '%artifact_ref_v1%'
   OR applies_to LIKE '%ready_signal_v1%'
   OR applies_to LIKE '%scheduler_lock_v1%'
   OR applies_to LIKE '%scheduler_lock_plan_v1%'
   OR note LIKE '%manager_request_v1%'
   OR note LIKE '%input_binding_v1%'
   OR note LIKE '%run_manifest_v1%'
   OR note LIKE '%run_step_v1%'
   OR note LIKE '%artifact_ref_v1%'
   OR note LIKE '%ready_signal_v1%'
   OR note LIKE '%scheduler_lock_v1%'
   OR note LIKE '%scheduler_lock_plan_v1%';
