-- Register benchmark dataset preparation artifacts and callable script.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'scr_EVALBMKDS001',
    'script',
    'TRADING_EVALUATION_PREPARE_BENCHMARK_DATASET',
    'command',
    'PYTHONPATH=src python3 scripts/evaluation/prepare_benchmark_dataset.py --contract $BENCHMARK_CONTRACT_JSON --output-root /root/projects/trading-storage/storage/benchmark --data-root /root/projects/trading-data/storage',
    '/root/projects/trading-evaluation/scripts/evaluation/prepare_benchmark_dataset.py',
    'trading-evaluation;benchmark_dataset_preparation;primary_benchmark_candidate;trading-storage;trading-data',
    'sync_artifact',
    'Prepare storage-owned benchmark dataset manifests and fail-closed feed task keys from a benchmark contract. The script scans local trading-data coverage but performs no provider calls, SQL mutation, benchmark freeze, model training, activation, broker execution, or account mutation.'
  ),
  (
    'art_EVALBMKDS001',
    'manifest_type',
    'BENCHMARK_DATASET_PREPARATION_MANIFEST',
    'json',
    'benchmark_dataset_preparation_manifest',
    'trading-storage/storage/benchmark/<contract_id>/dataset_manifest.json',
    'trading-storage;trading-evaluation;benchmark_dataset_preparation;primary_benchmark_candidate',
    'sync_artifact',
    'Storage runtime manifest describing component count, feed task count, local coverage scan counts, fail-closed task-key root, and safety flags for a benchmark dataset preparation bundle.'
  ),
  (
    'art_EVALBMKDS002',
    'artifact_type',
    'BENCHMARK_COMPONENT_MANIFEST',
    'file',
    'benchmark_component_manifest',
    'trading-storage/storage/benchmark/<contract_id>/component_manifest.csv',
    'trading-storage;trading-evaluation;benchmark_dataset_preparation;benchmark_component',
    'sync_artifact',
    'Storage runtime CSV listing benchmark component windows and metadata prepared from the accepted benchmark contract.'
  ),
  (
    'art_EVALBMKDS003',
    'artifact_type',
    'BENCHMARK_FEED_TASK_PLAN',
    'file',
    'benchmark_feed_task_plan',
    'trading-storage/storage/benchmark/<contract_id>/feed_task_plan.csv',
    'trading-storage;trading-evaluation;trading-data;benchmark_dataset_preparation;provider_dispatch_gate',
    'sync_artifact',
    'Storage runtime CSV listing per-component feed task requirements, fail-closed task-key paths, expected output refs, and local coverage status.'
  ),
  (
    'art_EVALBMKDS004',
    'artifact_type',
    'BENCHMARK_COVERAGE_SUMMARY',
    'file',
    'benchmark_coverage_summary',
    'trading-storage/storage/benchmark/<contract_id>/coverage_summary.csv',
    'trading-storage;trading-evaluation;benchmark_dataset_preparation;coverage_scan',
    'sync_artifact',
    'Storage runtime CSV summarizing required, available, and missing local feed coverage by benchmark component and source.'
  ),
  (
    'term_EVALBMKDS001',
    'term',
    'BENCHMARK_DATASET_PREPARATION_STATUS',
    'text',
    'prepared_not_dispatched',
    'trading-evaluation/docs/22_benchmark_dataset_preparation.md',
    'benchmark_dataset_preparation;provider_dispatch_gate;benchmark_freeze_gate',
    'sync_artifact',
    'Status meaning the benchmark dataset artifacts and fail-closed task keys have been prepared, but provider dispatch, benchmark freeze, SQL mutation, model training, and activation have not occurred.'
  ),
  (
    'term_EVALBMKDS002',
    'term',
    'BENCHMARK_PROVIDER_TASK_KEYS_FAIL_CLOSED_POLICY',
    'text',
    'task_keys_allow_live_provider_calls_false_until_provider_dispatch_gate',
    'trading-evaluation/docs/22_benchmark_dataset_preparation.md',
    'benchmark_dataset_preparation;provider_dispatch_gate;trading-data',
    'sync_artifact',
    'Benchmark dataset preparation task keys must set manager_controls.allow_live_provider_calls=false until a separate provider-dispatch gate enables live acquisition.'
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
