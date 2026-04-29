-- Split the overloaded generic status field into semantic status axes.

UPDATE trading_registry
SET key = 'DATA_KIND_TEMPLATE_STATUS',
    payload = 'data_kind_template_status',
    applies_to = 'data_kind_template',
    note = 'source README data-kind implementation status such as live-confirmed, implemented, derived-implemented, entitlement-blocked, adapter-needed, or planned. Classification value should use a stable lowercase token vocabulary unless the source contract explicitly requires another reviewed encoding.'
WHERE id = 'fld_EKIND004';

INSERT INTO trading_registry (
  id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note
) VALUES (
  'fld_DTRS001',
  'classification_field',
  'DATA_TASK_RUN_STATUS',
  'field_name',
  'data_task_run_status',
  'storage/templates/data_tasks/completion_receipt.json',
  'data_task_completion_receipt_run',
  'sync_artifact',
  'data task run execution status such as succeeded or failed. Classification value should use a stable lowercase token vocabulary unless the source contract explicitly requires another reviewed encoding.'
);
