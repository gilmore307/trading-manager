-- Normalize durable control-plane SQL contract_type defaults/checks to stable semantic names.
-- The active naming policy keeps version information in schema metadata, not in business contract ids.

ALTER TABLE trading_manager.manager_request DROP CONSTRAINT IF EXISTS manager_request_contract_type_check;
UPDATE trading_manager.manager_request
SET contract_type = 'manager_request'
WHERE contract_type = 'manager_request_v1';
ALTER TABLE trading_manager.manager_request ALTER COLUMN contract_type SET DEFAULT 'manager_request';
ALTER TABLE trading_manager.manager_request
  ADD CONSTRAINT manager_request_contract_type_check CHECK (contract_type = 'manager_request');

ALTER TABLE trading_manager.input_binding DROP CONSTRAINT IF EXISTS input_binding_contract_type_check;
UPDATE trading_manager.input_binding
SET contract_type = 'input_binding'
WHERE contract_type = 'input_binding_v1';
ALTER TABLE trading_manager.input_binding ALTER COLUMN contract_type SET DEFAULT 'input_binding';
ALTER TABLE trading_manager.input_binding
  ADD CONSTRAINT input_binding_contract_type_check CHECK (contract_type = 'input_binding');

ALTER TABLE trading_manager.run_manifest DROP CONSTRAINT IF EXISTS run_manifest_contract_type_check;
UPDATE trading_manager.run_manifest
SET contract_type = 'run_manifest'
WHERE contract_type = 'run_manifest_v1';
ALTER TABLE trading_manager.run_manifest ALTER COLUMN contract_type SET DEFAULT 'run_manifest';
ALTER TABLE trading_manager.run_manifest
  ADD CONSTRAINT run_manifest_contract_type_check CHECK (contract_type = 'run_manifest');

ALTER TABLE trading_manager.run_step DROP CONSTRAINT IF EXISTS run_step_contract_type_check;
UPDATE trading_manager.run_step
SET contract_type = 'run_step'
WHERE contract_type = 'run_step_v1';
ALTER TABLE trading_manager.run_step ALTER COLUMN contract_type SET DEFAULT 'run_step';
ALTER TABLE trading_manager.run_step
  ADD CONSTRAINT run_step_contract_type_check CHECK (contract_type = 'run_step');

ALTER TABLE trading_manager.artifact_ref DROP CONSTRAINT IF EXISTS artifact_ref_contract_type_check;
UPDATE trading_manager.artifact_ref
SET contract_type = 'artifact_ref'
WHERE contract_type = 'artifact_ref_v1';
ALTER TABLE trading_manager.artifact_ref ALTER COLUMN contract_type SET DEFAULT 'artifact_ref';
ALTER TABLE trading_manager.artifact_ref
  ADD CONSTRAINT artifact_ref_contract_type_check CHECK (contract_type = 'artifact_ref');

ALTER TABLE trading_manager.ready_signal DROP CONSTRAINT IF EXISTS ready_signal_contract_type_check;
UPDATE trading_manager.ready_signal
SET contract_type = 'ready_signal'
WHERE contract_type = 'ready_signal_v1';
ALTER TABLE trading_manager.ready_signal ALTER COLUMN contract_type SET DEFAULT 'ready_signal';
ALTER TABLE trading_manager.ready_signal
  ADD CONSTRAINT ready_signal_contract_type_check CHECK (contract_type = 'ready_signal');

ALTER TABLE trading_manager.failure_register DROP CONSTRAINT IF EXISTS failure_register_contract_type_check;
UPDATE trading_manager.failure_register
SET contract_type = 'manager_failure_register'
WHERE contract_type = 'manager_failure_register_v1';
ALTER TABLE trading_manager.failure_register ALTER COLUMN contract_type SET DEFAULT 'manager_failure_register';
ALTER TABLE trading_manager.failure_register
  ADD CONSTRAINT failure_register_contract_type_check CHECK (contract_type = 'manager_failure_register');

UPDATE trading_registry
SET note = 'SQL-backed manager/control-plane contract tables use stable unversioned contract_type values; schema versioning belongs in schema metadata and migration history.',
    applies_to = 'manager_request;input_binding;run_manifest;run_step;artifact_ref;ready_signal;manager_failure_register;stable_semantic_names',
    updated_at = NOW()
WHERE id = 'cfg_MSH001';
