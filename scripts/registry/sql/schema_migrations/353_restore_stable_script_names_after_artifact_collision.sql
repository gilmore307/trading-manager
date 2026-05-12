-- Restore script rows whose stable names collided with formerly version-suffixed artifact-type rows.
-- Artifact-type rows keep explicit *_ARTIFACT keys; callable script entrypoints keep the plain semantic script keys.

UPDATE trading_registry
SET key = 'MANAGER_MODEL_TRAINING_WORKFLOW_PLAN',
    updated_at = NOW()
WHERE id = 'scr_MMTW001'
  AND key = 'MANAGER_MODEL_TRAINING_WORKFLOW_PLAN_ARTIFACT';

UPDATE trading_registry
SET key = 'MANAGER_TASK_SYSTEM_REHEARSAL',
    updated_at = NOW()
WHERE id = 'scr_MTS004'
  AND key = 'MANAGER_TASK_SYSTEM_REHEARSAL_ARTIFACT';
