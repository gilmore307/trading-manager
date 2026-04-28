-- Merge remaining duplicate field payload rows where the same concrete field name
-- had multiple registry entries. Config rows with identical JSON payloads remain
-- separate because each points to a distinct config artifact/path.

UPDATE trading_registry
SET
  key = 'BUNDLE',
  applies_to = 'data_kind_template;data_task_key;data_task_completion_receipt',
  path = 'trading-data/storage/templates/data_kinds/README.md',
  note = 'canonical bundle field for data-kind templates, data task keys, and completion receipts'
WHERE kind = 'field' AND key = 'DATA_KIND_TEMPLATE_BUNDLE';

UPDATE trading_registry
SET
  key = 'STATUS',
  applies_to = 'data_kind_template;data_task_completion_receipt_run',
  path = 'trading-data/storage/templates/data_kinds/README.md',
  note = 'canonical status field for data-kind templates and data task run receipts'
WHERE kind = 'field' AND key = 'DATA_KIND_TEMPLATE_STATUS';

UPDATE trading_registry
SET
  key = 'ID',
  applies_to = 'trading_registry;event_timeline_template',
  path = NULL,
  note = 'canonical id field for registry rows and source/event timeline rows where the concrete column is id'
WHERE kind = 'field' AND key = 'REGISTRY_ITEM_ID';

DELETE FROM trading_registry
WHERE kind = 'field'
  AND key IN (
    'DATA_TASK_BUNDLE',
    'DATA_TASK_RUN_STATUS',
    'TIMELINE_ID'
  );
