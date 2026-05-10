-- Register storage lifecycle policy, request, receipt, manifest, and state vocabulary.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'cfg_SLC001',
    'config',
    'STORAGE_LIFECYCLE_POLICY',
    'text',
    'storage_lifecycle_default_v1;promoted_model_bodies_keep_forever;regenerable_intermediates_ttl_delete;source_data_compress_before_delete;sql_detail_export_archive_only;manifest_receipt_required',
    'trading-storage/docs/91_storage_lifecycle_policy.md',
    'trading-storage;storage_lifecycle;retention;compression;archive;delete;restore',
    'sync_artifact',
    'Storage-owned lifecycle policy. Manager may request or observe lifecycle work, but storage owns compression, archive, protected-set checks, deletion, restore, receipts, and tombstones.'
  ),
  (
    'cfg_SLC002',
    'config',
    'STORAGE_PROTECTED_SET_POLICY',
    'text',
    'promoted_model_lineage;active_model_lineage;active_review_refs;manager_artifact_refs;ready_signal_refs;dataset_snapshot_split_manifests;open_task_run_manifests;active_target_chain;sql_online_dependencies;manual_pins;unknown_metadata',
    'trading-storage/docs/93_protected_set.md',
    'trading-storage;storage_lifecycle;protected_set;delete_quarantine;sql_archive',
    'sync_artifact',
    'Protected-set policy for lifecycle safety. Deletion and SQL detach/drop require protected-set clearance, quarantine, and final recheck.'
  ),
  (
    'cfg_SLC003',
    'config',
    'STORAGE_LIFECYCLE_STATE_VALUES',
    'text',
    'hot;warm;cold_compressible;cold_compressed;archivable;archived;delete_candidate;quarantined_for_delete;deleted;restored',
    'trading-storage/docs/91_storage_lifecycle_policy.md',
    'trading-storage;storage_lifecycle;artifact_index;lifecycle_state',
    'sync_artifact',
    'Accepted lifecycle state values for storage artifact lifecycle planning and receipts.'
  ),
  (
    'cfg_SLC004',
    'config',
    'STORAGE_RETENTION_POLICY_FORMAT',
    'text',
    'declarative_yaml_or_json;policy_id;rule_id;selector;action;ttl;codec;protected_set_required;quarantine_days;restore_smoke_required',
    'trading-storage/docs/91_storage_lifecycle_policy.md',
    'trading-storage;storage_lifecycle;retention_policy;policy_review',
    'sync_artifact',
    'Retention behavior should be reviewed as declarative policy instead of hidden script branches.'
  ),
  (
    'cfg_SLC005',
    'config',
    'STORAGE_READ_MODE_VALUES',
    'text',
    'direct_readable;restore_required;metadata_only',
    'trading-storage/docs/92_artifact_index.md',
    'trading-storage;artifact_index;compression;archive;restore',
    'sync_artifact',
    'Read-mode values distinguishing direct-readable compressed artifacts from archives that require restore.'
  ),
  (
    'cfg_SLC006',
    'config',
    'STORAGE_REPRODUCIBILITY_CLASS_VALUES',
    'text',
    'non_reproducible;provider_window_limited;expensive_to_reproduce;reproducible_with_manifest;fully_reproducible;unknown',
    'trading-storage/docs/92_artifact_index.md',
    'trading-storage;artifact_index;retention_policy;delete_policy',
    'sync_artifact',
    'Artifact reproducibility classes used by lifecycle policy. Unknown/non-reproducible/provider-window-limited/expensive artifacts are treated conservatively.'
  ),
  (
    'cfg_SLC007',
    'config',
    'STORAGE_SUMMARIZE_THEN_ARCHIVE_DETAIL_POLICY',
    'text',
    'online_summary_retained;row_level_detail_archived;archive_ref_recorded;restore_required_for_detail',
    'trading-storage/docs/94_compression_archive.md',
    'trading-storage;sql_archive;model_eval_detail;feature_detail;source_detail;dashboard_summary',
    'sync_artifact',
    'Large SQL/detail families may retain online summaries while row-level detail is archived and restored only when needed.'
  ),
  (
    'req_SLC001',
    'request_type',
    'STORAGE_LIFECYCLE_REQUEST_V1',
    'text',
    'storage_lifecycle_request_v1',
    'trading-storage/docs/91_storage_lifecycle_policy.md',
    'manager_request_v1;trading-storage;storage_lifecycle;compression;archive;delete;restore',
    'sync_artifact',
    'Request type for manager/operator requests to plan or execute reviewed storage lifecycle work. Manager requests; storage executes.'
  ),
  (
    'mft_SLC001',
    'manifest_type',
    'COMPRESSION_RECEIPT_V1',
    'text',
    'compression_receipt_v1',
    'trading-storage/docs/95_lifecycle_receipts.md',
    'trading-storage;storage_lifecycle;compression;artifact_ref_v1',
    'sync_artifact',
    'Receipt emitted after compression validation succeeds or fails.'
  ),
  (
    'mft_SLC002',
    'manifest_type',
    'ARCHIVE_RECEIPT_V1',
    'text',
    'archive_receipt_v1',
    'trading-storage/docs/95_lifecycle_receipts.md',
    'trading-storage;storage_lifecycle;archive;sql_archive;artifact_ref_v1',
    'sync_artifact',
    'Receipt emitted after file or SQL archive creation and validation.'
  ),
  (
    'mft_SLC003',
    'manifest_type',
    'DELETION_RECEIPT_V1',
    'text',
    'deletion_receipt_v1',
    'trading-storage/docs/95_lifecycle_receipts.md',
    'trading-storage;storage_lifecycle;delete;quarantine;artifact_tombstone_v1',
    'sync_artifact',
    'Receipt emitted only after quarantine and final protected-set recheck pass.'
  ),
  (
    'mft_SLC004',
    'manifest_type',
    'RESTORE_RECEIPT_V1',
    'text',
    'restore_receipt_v1',
    'trading-storage/docs/95_lifecycle_receipts.md',
    'trading-storage;storage_lifecycle;restore;restore_verifier',
    'sync_artifact',
    'Receipt emitted after restore verification or materialized restore.'
  ),
  (
    'mft_SLC005',
    'manifest_type',
    'COMPRESSION_MANIFEST_V1',
    'text',
    'compression_manifest_v1',
    'trading-storage/docs/95_lifecycle_receipts.md',
    'trading-storage;storage_lifecycle;compression;restore_manifest_v1',
    'sync_artifact',
    'Manifest describing compressed file/object artifacts, checksums, codec, read mode, lineage refs, and restore command.'
  ),
  (
    'mft_SLC006',
    'manifest_type',
    'SQL_ARCHIVE_MANIFEST_V1',
    'text',
    'sql_archive_manifest_v1',
    'trading-storage/docs/95_lifecycle_receipts.md',
    'trading-storage;storage_lifecycle;sql_archive;restore_manifest_v1',
    'sync_artifact',
    'Manifest describing exported SQL table/partition archives, schema/data exports, checksums, row counts, and restore command.'
  ),
  (
    'mft_SLC007',
    'manifest_type',
    'RESTORE_MANIFEST_V1',
    'text',
    'restore_manifest_v1',
    'trading-storage/docs/95_lifecycle_receipts.md',
    'trading-storage;storage_lifecycle;restore;archive;compression',
    'sync_artifact',
    'Manifest describing how to restore a compressed or archived storage artifact.'
  ),
  (
    'art_SLC001',
    'artifact_type',
    'ARTIFACT_TOMBSTONE_V1',
    'text',
    'artifact_tombstone_v1',
    'trading-storage/docs/95_lifecycle_receipts.md',
    'trading-storage;storage_lifecycle;delete;artifact_index',
    'sync_artifact',
    'Minimal post-deletion artifact record preserving prior path, checksum, size, deletion receipt, policy, reason codes, and restore possibility.'
  ),
  (
    'art_SLC002',
    'shared_artifact',
    'STORAGE_ARTIFACT_INDEX',
    'text',
    'artifact_index;dependency_graph',
    'trading-storage/docs/92_artifact_index.md',
    'trading-storage;artifact_index;dependency_graph;protected_set;storage_lifecycle',
    'sync_artifact',
    'Storage-owned artifact index and dependency graph required before production lifecycle mutation.'
  )
ON CONFLICT (id) DO UPDATE
SET kind = EXCLUDED.kind,
    key = EXCLUDED.key,
    payload_format = EXCLUDED.payload_format,
    payload = EXCLUDED.payload,
    path = EXCLUDED.path,
    applies_to = EXCLUDED.applies_to,
    artifact_sync_policy = EXCLUDED.artifact_sync_policy,
    note = EXCLUDED.note,
    updated_at = NOW();
