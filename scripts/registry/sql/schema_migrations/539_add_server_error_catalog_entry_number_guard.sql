-- Guard owner-facing server error numbers at the SQL catalog layer.

CREATE UNIQUE INDEX IF NOT EXISTS idx_server_error_catalog_entry_number_unique
ON trading_manager.server_error_catalog(error_number)
WHERE contract_type = 'server_error_catalog_entry';

UPDATE trading_registry
SET payload = 'server_error_catalog_sql_primary;entry_error_number_unique;request_and_diagnosis_artifacts_remain_storage_refs;legacy_jsonl_read_compatibility_only',
    note = 'Server error catalog numbering, deduplication, and owner follow-up facts are SQL control-plane rows. Entry rows have unique owner-facing ERR numbers; occurrence rows may reuse an ERR number for deduplicated repeats. Storage/runtime files are evidence artifacts, not the canonical catalog.'
WHERE key = 'MANAGER_AGENT_ERROR_SQL_CATALOG_POLICY';
