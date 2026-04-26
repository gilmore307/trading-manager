-- Register minimal data task key and completion receipt JSON field names.
-- Target engine: PostgreSQL.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, note)
VALUES
  ('fld_PS5T5LFZ', 'field', 'DATA_TASK_ID', 'field_name', 'task_id', NULL, 'data_task_key;data_task_completion_receipt', 'stable manager-issued data task identifier shared by task key and task-level completion receipt'),
  ('fld_7DDUFDLJ', 'field', 'DATA_TASK_BUNDLE', 'field_name', 'bundle', NULL, 'data_task_key;data_task_completion_receipt', 'data acquisition bundle name shared by task key and task-level completion receipt'),
  ('fld_FJF5ZAJ5', 'field', 'DATA_TASK_CREDENTIAL_CONFIG_ID', 'field_name', 'credential_config_id', NULL, 'data_task_key', 'optional registry config id for provider/source credentials required by a data task'),
  ('fld_E7E3JEKV', 'field', 'DATA_TASK_PARAMS', 'field_name', 'params', NULL, 'data_task_key', 'bundle-specific task parameters consumed by the data source pipeline'),
  ('fld_PPBXKTON', 'field', 'DATA_TASK_OUTPUT_ROOT', 'field_name', 'output_root', NULL, 'data_task_key', 'stable development output root for all runs of a data task'),
  ('fld_44PMLSPO', 'field', 'DATA_TASK_RECEIPT_RUNS', 'field_name', 'runs', NULL, 'data_task_completion_receipt', 'array of per-run evidence entries in a task-level data completion receipt'),
  ('fld_F3FORVEW', 'field', 'DATA_TASK_RUN_ID', 'field_name', 'run_id', NULL, 'data_task_completion_receipt_run', 'identifier for one invocation of a stable data task key'),
  ('fld_IBWL6MAT', 'field', 'DATA_TASK_RUN_STATUS', 'field_name', 'status', NULL, 'data_task_completion_receipt_run', 'per-run completion status value'),
  ('fld_MWVTFVQC', 'field', 'DATA_TASK_RUN_STARTED_AT', 'field_name', 'started_at', NULL, 'data_task_completion_receipt_run', 'per-run start timestamp'),
  ('fld_JA6LF4YX', 'field', 'DATA_TASK_RUN_COMPLETED_AT', 'field_name', 'completed_at', NULL, 'data_task_completion_receipt_run', 'per-run completion timestamp'),
  ('fld_U3G3BLPO', 'field', 'DATA_TASK_RUN_OUTPUT_DIR', 'field_name', 'output_dir', NULL, 'data_task_completion_receipt_run', 'development output directory for one data task run'),
  ('fld_ES5OZEMA', 'field', 'DATA_TASK_RUN_OUTPUTS', 'field_name', 'outputs', NULL, 'data_task_completion_receipt_run', 'per-run output file or artifact references'),
  ('fld_AN2VVTDU', 'field', 'DATA_TASK_RUN_ROW_COUNTS', 'field_name', 'row_counts', NULL, 'data_task_completion_receipt_run', 'per-run output row counts by output name'),
  ('fld_7FW3A4DF', 'field', 'DATA_TASK_RUN_ERROR', 'field_name', 'error', NULL, 'data_task_completion_receipt_run', 'per-run error detail; null when run succeeds')
ON CONFLICT (id) DO UPDATE
SET
  kind = EXCLUDED.kind,
  key = EXCLUDED.key,
  payload_format = EXCLUDED.payload_format,
  payload = EXCLUDED.payload,
  path = EXCLUDED.path,
  applies_to = EXCLUDED.applies_to,
  note = EXCLUDED.note;
