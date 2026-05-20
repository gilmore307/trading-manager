-- Register benchmark lifecycle retention terms.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'term_STORBENCH001',
    'term',
    'BENCHMARK_RESULT_SUMMARY_PROTECTED_REASON',
    'text',
    'benchmark_result_summary',
    'trading-storage/src/trading_storage/artifact_index.py;trading-storage/src/trading_storage/protected_set.py;trading-storage/docs/20_storage_lifecycle_policy.md',
    'trading-storage;storage_lifecycle;benchmark;protected_set;model_pipeline_benchmark_result_summary',
    'sync_artifact',
    'Protected-set reason for permanent model-pipeline benchmark result summaries, scorecards, baseline comparisons, manifest refs, and receipt evidence. It does not imply keeping every model-specific downloaded benchmark file.'
  ),
  (
    'term_STORBENCH002',
    'term',
    'BENCHMARK_REUSABLE_INPUT_RETENTION',
    'text',
    'benchmark_layer_01_02_and_event_news_inputs_retain_or_compress',
    'trading-storage/src/trading_storage/artifact_index.py;trading-storage/docs/20_storage_lifecycle_policy.md',
    'trading-storage;storage_lifecycle;benchmark;layer_01;layer_02;event_news;compress_and_retain',
    'sync_artifact',
    'Benchmark Layer 1, Layer 2, and event/news inputs are reusable benchmark/replay data. They should be retained or compressed/archived rather than deleted after one model pipeline benchmark run.'
  ),
  (
    'term_STORBENCH003',
    'term',
    'BENCHMARK_MODEL_SPECIFIC_DOWNLOAD_CLEANUP',
    'text',
    'model_specific_benchmark_downloads_ttl_delete_after_benchmark_close',
    'trading-storage/src/trading_storage/artifact_index.py;trading-storage/docs/20_storage_lifecycle_policy.md',
    'trading-storage;storage_lifecycle;benchmark;model_specific_download;option_snapshot;ttl_delete_allowed',
    'sync_artifact',
    'Model-specific benchmark downloads, such as one-off point-in-time option snapshots fetched only for one pipeline benchmark run, may become TTL cleanup candidates after benchmark close once summaries, manifests, receipts, and reusable inputs are retained.'
  ),
  (
    'term_STORLIFE001',
    'term',
    'KEEP_FOREVER_RETENTION_PROTECTED_REASON',
    'text',
    'keep_forever_retention',
    'trading-storage/src/trading_storage/artifact_index.py;trading-storage/src/trading_storage/protected_set.py',
    'trading-storage;storage_lifecycle;protected_set;keep_forever;retention_class',
    'sync_artifact',
    'Generic protected-set reason for non-benchmark artifacts explicitly classified with retention_class keep_forever.'
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
