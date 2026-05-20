-- Register benchmark one-shot acquisition runner.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'scr_EVALBMKACQ001',
    'script',
    'TRADING_EVALUATION_RUN_BENCHMARK_ACQUISITION',
    'command',
    'PYTHONPATH=src python3 scripts/evaluation/run_benchmark_acquisition.py --dataset-root $BENCHMARK_DATASET_ROOT --source-id $SOURCE_ID --limit $LIMIT',
    '/root/projects/trading-evaluation/scripts/evaluation/run_benchmark_acquisition.py',
    'trading-evaluation;benchmark_dataset_preparation;one_shot_benchmark_acquisition;trading-data;trading-storage',
    'sync_artifact',
    'Plans or executes bounded one-shot benchmark feed acquisitions from feed_acquisition_plan.csv. It writes task payloads and progress logs under the benchmark dataset root, performs live provider calls only with --execute, and creates no manager request rows.'
  )
ON CONFLICT (key) DO UPDATE
SET payload = EXCLUDED.payload,
    path = EXCLUDED.path,
    applies_to = EXCLUDED.applies_to,
    artifact_sync_policy = EXCLUDED.artifact_sync_policy,
    note = EXCLUDED.note,
    updated_at = NOW();
