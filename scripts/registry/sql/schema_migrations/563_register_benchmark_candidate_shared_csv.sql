-- Register the storage-owned shared CSV view of the primary benchmark candidate.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'out_EVALBMKCSV001',
    'shared_artifact',
    'EVALUATION_PRIMARY_BENCHMARK_CANDIDATE_SHARED_CSV',
    'file',
    'trading-storage/main/shared/evaluation_primary_benchmark_candidate.csv',
    '/root/projects/trading-storage/main/shared/evaluation_primary_benchmark_candidate.csv',
    'trading-storage;trading-evaluation;benchmark_contract;primary_benchmark_candidate;promotion_eligibility;horizontal_comparison',
    'sync_artifact',
    'Storage-owned shared static CSV view of the final primary benchmark candidate. The source contract remains trading-evaluation/benchmarks/primary_benchmark_candidate_20260519.json; the CSV lists component windows, fixed weights, time buckets, sector coverage tags, event coverage tags, data-availability tags, target-context refs, stress exceptions, and training-exclusion reasons.'
  ),
  (
    'term_EVALBMKCSV001',
    'term',
    'EVALUATION_PRIMARY_BENCHMARK_CANDIDATE_CSV_CONTRACT',
    'text',
    'evaluation_primary_benchmark_candidate_csv',
    'trading-storage/main/shared/evaluation_primary_benchmark_candidate.csv',
    'benchmark_contract;primary_benchmark_candidate;shared_static_assets',
    'sync_artifact',
    'CSV contract for reviewing and referencing the accepted final candidate benchmark composition before it is frozen.'
  ),
  (
    'fld_EVALBMKCSV001',
    'field',
    'BENCHMARK_CANDIDATE_STATUS',
    'field_name',
    'candidate_status',
    'trading-storage/main/shared/evaluation_primary_benchmark_candidate.csv',
    'evaluation_primary_benchmark_candidate_csv;primary_benchmark_candidate',
    'sync_artifact',
    'Candidate lifecycle status such as final_candidate_not_frozen; freezing requires a separate accepted benchmark contract decision.'
  ),
  (
    'fld_EVALBMKCSV002',
    'field',
    'BENCHMARK_TIME_BUCKET_ID',
    'field_name',
    'time_bucket_id',
    'trading-storage/main/shared/evaluation_primary_benchmark_candidate.csv',
    'evaluation_primary_benchmark_candidate_csv;balanced_time_bucket_panel',
    'sync_artifact',
    'Stable identifier for the benchmark time allocation bucket containing the component.'
  ),
  (
    'fld_EVALBMKCSV003',
    'field',
    'BENCHMARK_SECTOR_COVERAGE_TAGS',
    'field_name',
    'sector_coverage_tags',
    'trading-storage/main/shared/evaluation_primary_benchmark_candidate.csv',
    'evaluation_primary_benchmark_candidate_csv;sector_coverage_required',
    'sync_artifact',
    'Semicolon-separated sector coverage tags used to prove the benchmark covers consumer, entertainment/media, and other required sectors.'
  ),
  (
    'fld_EVALBMKCSV004',
    'field',
    'BENCHMARK_EVENT_COVERAGE_TAGS',
    'field_name',
    'event_coverage_tags',
    'trading-storage/main/shared/evaluation_primary_benchmark_candidate.csv',
    'evaluation_primary_benchmark_candidate_csv;event_driven_coverage_required;earnings_crossing_coverage_required',
    'sync_artifact',
    'Semicolon-separated event coverage tags used to prove the benchmark covers earnings-crossing and event-driven windows.'
  ),
  (
    'fld_EVALBMKCSV005',
    'field',
    'BENCHMARK_TRAINING_EXCLUSION_REASON',
    'field_name',
    'training_exclusion_reason',
    'trading-storage/main/shared/evaluation_primary_benchmark_candidate.csv',
    'evaluation_primary_benchmark_candidate_csv;target_window_training_exclusion_required',
    'sync_artifact',
    'Plain reason tying a component window to the same-target training-fold exclusion guardrail.'
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
